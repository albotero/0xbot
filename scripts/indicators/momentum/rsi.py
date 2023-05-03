from pandas import DataFrame


def rsi(data: DataFrame, periods: int = 14) -> str:
    ''' Relative Strength Index

    Return Header: RSI '''
    # Calculate U and D
    u = (data["close"] - data["close"].shift(1)).clip(lower=0)
    d = (data["close"].shift(1) - data["close"]).clip(lower=0)
    # Smooth U and D
    ema_u = u.ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    ema_d = d.ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    # Calculate Relative Strength
    rs = ema_u / ema_d
    rsi = rs.apply(lambda row: 100 - (100 / (1 + row)))
    header = f"rsi-{periods}"
    data[header] = rsi
    return header
