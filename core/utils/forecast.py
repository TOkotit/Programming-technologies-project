from collections import defaultdict
from datetime import date
import math


def _month_key(d):
    return d.year, d.month


def _add_months(d, n):
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return date(y, m, 1)


def forecast_monthly(invoices, months_ahead=6, alpha=0.4):
    """
    Lightweight forecast without heavy libraries.
    Model: trend + seasonality + exponential smoothing
    """

    # --- 1. Aggregate invoices by month ---
    monthly = defaultdict(float)
    for inv in invoices:
        k = _month_key(inv.date)
        monthly[k] += float(inv.amount)

    if not monthly:
        return {"historic": [], "forecast": []}

    months = sorted(monthly.keys())
    values = [monthly[m] for m in months]

    # --- 2. Exponential smoothing (EMA) ---
    smoothed = []
    for v in values:
        if not smoothed:
            smoothed.append(v)
        else:
            smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])

    # --- 3. Linear trend (least squares) ---
    n = len(smoothed)
    x = list(range(n))
    y = smoothed

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0
    intercept = y_mean - slope * x_mean

    # --- 4. Seasonality (month factors) ---
    season = defaultdict(list)
    for (y_, m_), v in zip(months, smoothed):
        season[m_].append(v)

    season_avg = {m: sum(vs) / len(vs) for m, vs in season.items()}
    overall_avg = sum(smoothed) / len(smoothed)

    season_factor = {
        m: (season_avg[m] / overall_avg if overall_avg else 1.0)
        for m in season_avg
    }

    # --- 5. Forecast ---
    last_month = date(months[-1][0], months[-1][1], 1)
    forecast = []

    for i in range(1, months_ahead + 1):
        base = slope * (n + i) + intercept
        month_num = _add_months(last_month, i).month
        factor = season_factor.get(month_num, 1.0)
        value = max(0.0, base * factor)

        forecast.append({
            "month": _add_months(last_month, i),
            "value": round(value, 2)
        })

    # --- Output format (compatible with your dashboard) ---
    historic = [
        {"month": date(y, m, 1), "value": round(v, 2)}
        for (y, m), v in zip(months, values)
    ]

    return {
        "historic": historic,
        "forecast": forecast
    }
