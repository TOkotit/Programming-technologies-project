import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression




def forecast_monthly(invoices_qs, months_ahead=6):
    """Возвращает dict с 'historic' и 'forecast' DataFrame'ами.
    invoices_qs — queryset или list/dict с полями date и amount.
    """
    df = pd.DataFrame(list(invoices_qs.values('date', 'amount')))
    if df.empty:
        return {'historic': pd.DataFrame(), 'forecast': pd.DataFrame()}
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly = monthly.sort_values('month')
    monthly['idx'] = np.arange(len(monthly))
    X = monthly[['idx']].values
    y = monthly['amount'].values
    model = LinearRegression()
    model.fit(X, y)
    future_idx = np.arange(len(monthly), len(monthly) + months_ahead).reshape(-1, 1)
    preds = model.predict(future_idx)
    future_months = pd.date_range(start=monthly['month'].iloc[-1] + pd.offsets.MonthBegin(1), periods=months_ahead, freq='MS')
    historic = monthly[['month', 'amount']].rename(columns={'amount': 'value'})
    forecast = pd.DataFrame({'month': future_months, 'value': preds})
    return {'historic': historic, 'forecast': forecast}