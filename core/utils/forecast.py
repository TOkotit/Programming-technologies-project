import numpy as np
from scipy.optimize import minimize
from datetime import date
from django.db.models.functions import TruncMonth
from django.db.models import Sum


def _month_add(dt, months):
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def initial_trend(series, slen):
    sum_val = 0.0
    for i in range(slen):
        sum_val += float(series[i + slen] - series[i]) / slen
    return sum_val / slen


def initial_seasonal_components(series, slen):
    seasonals = {}
    season_averages = []
    n_seasons = len(series) // slen
    for j in range(n_seasons):
        season_averages.append(sum(series[slen * j:slen * j + slen]) / float(slen))
    for i in range(slen):
        sum_of_vals_over_avg = 0.0
        for j in range(n_seasons):
            sum_of_vals_over_avg += series[slen * j + i] - season_averages[j]
        seasonals[i] = sum_of_vals_over_avg / n_seasons
    return seasonals


def triple_exponential_smoothing(series, slen, n_preds, alpha, beta, gamma):
    result = []
    seasonals = initial_seasonal_components(series, slen)
    for i in range(len(series) + n_preds):
        if i == 0:
            smooth = series[0]
            trend = initial_trend(series, slen)
            result.append(series[0])
            continue
        if i >= len(series):  # Прогноз
            m = i - len(series) + 1
            result.append((smooth + m * trend) + seasonals[i % slen])
        else:  # Обучение
            val = series[i]
            last_smooth, smooth = smooth, alpha * (val - seasonals[i % slen]) + (1 - alpha) * (smooth + trend)
            trend = beta * (smooth - last_smooth) + (1 - beta) * trend
            seasonals[i % slen] = gamma * (val - smooth) + (1 - gamma) * seasonals[i % slen]
            result.append(smooth + trend + seasonals[i % slen])
    return result


def forecast_monthly(invoices_qs, months_ahead=6):
    # 1. Подготовка данных через NumPy
    monthly = (
        invoices_qs
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    points = [(r['month'], float(r['total'] or 0)) for r in monthly if r['month']]
    if len(points) < 4:  # Для Хольта-Уинтерса нужно хотя бы немного данных
        return {'historic': [], 'forecast': []}

    series = np.array([p[1] for p in points])
    dates = [p[0] for p in points]
    slen = 3  # Предположим квартальную сезонность для малых данных, или 12 для годовой

    # 2. Оптимизация параметров alpha, beta, gamma через SciPy
    def objective(params):
        a, b, g = params
        preds = triple_exponential_smoothing(series, slen, 0, a, b, g)
        return np.sqrt(np.mean((series - preds) ** 2))  # RMSE

    opt = minimize(objective, x0=[0.1, 0.1, 0.1], bounds=((0, 1), (0, 1), (0, 1)))
    a_opt, b_opt, g_opt = opt.x

    # 3. Генерация прогноза
    full_series = triple_exponential_smoothing(series, slen, months_ahead, a_opt, b_opt, g_opt)

    # 4. Расчет доверительного интервала (упрощенно через std)
    std_dev = np.std(series - np.array(full_series[:len(series)]))

    historic = []
    for i in range(len(series)):
        historic.append({
            'month': dates[i].strftime('%Y-%m'),
            'value': round(series[i], 2)
        })

    forecast = []
    last_date = dates[-1]
    for i in range(months_ahead):
        val = full_series[len(series) + i]
        forecast.append({
            'month': _month_add(last_date, i + 1).strftime('%Y-%m'),
            'value': round(max(0, val), 2),
            'upper': round(max(0, val + 1.96 * std_dev), 2),  # 95% интервал
            'lower': round(max(0, val - 1.96 * std_dev), 2)
        })

    return {'historic': historic, 'forecast': forecast, 'rmse': round(opt.fun, 2)}