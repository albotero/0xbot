from pandas import DataFrame


def rsi(data: DataFrame, periods: int = 14) -> str:
    """Relative Strength Index

    Return Header: RSI"""
    # Calculate U and D
    u = (data["close"] - data["close"].shift(1)).clip(lower=0)
    d = (data["close"].shift(1) - data["close"]).clip(lower=0)
    # Smooth U and D
    ema_u = u.ewm(span=periods, adjust=False).mean()
    ema_d = d.ewm(span=periods, adjust=False).mean()
    # Calculate Relative Strength
    rs = ema_u / ema_d
    _rsi = rs.apply(lambda val: 100 - (100 / (1 + val)))
    # Update DataFrame
    header = f"rsi({periods})"
    data[header] = _rsi
    return header
