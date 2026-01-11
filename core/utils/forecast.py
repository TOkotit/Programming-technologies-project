import datetime


def forecast_monthly(invoices_qs, months_ahead=6):
    data = {}
    for inv in invoices_qs.values('date', 'amount'):
        m = inv['date'].replace(day=1)
        data[m] = data.get(m, 0) + float(inv['amount'])

    sorted_months = sorted(data.keys())
    if not sorted_months:
        return {'historic': [], 'forecast': []}

    y = [data[m] for m in sorted_months]
    x = list(range(len(y)))
    n = len(x)

    if n > 1:
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xx = sum(i*i for i in x)
        sum_xy = sum(i*j for i, j in zip(x, y))

        m_slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        b_intercept = (sum_y - m_slope * sum_x) / n
    else:
        m_slope = 0
        b_intercept = y[0] if y else 0

    historic = [{'month': m.strftime('%Y-%m-%d'), 'value': data[m]} for m in sorted_months]

    forecast = []
    last_month = sorted_months[-1]
    for i in range(1, months_ahead + 1):
        new_month = (last_month.replace(day=28) + datetime.timedelta(days=5)).replace(day=1)
        pred_value = m_slope * (n + i - 1) + b_intercept
        forecast.append({'month': new_month.strftime('%Y-%m-%d'), 'value': max(0, pred_value)})
        last_month = new_month

    return {'historic': historic, 'forecast': forecast}