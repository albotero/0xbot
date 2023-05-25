from pandas import DataFrame


def dema(data: DataFrame, periods: int) -> str:
    """Double Exponential Moving Average

    Return Header: DEMA"""
    # Calculate EMA from the data
    ema = data["close"].ewm(span=periods, adjust=False).mean()
    #  Calculate EMA from the previous calculated EMA
    _dema = ema.ewm(span=periods, adjust=False).mean()
    # Update DataFrame
    header = f"dema({periods})"
    data[header] = _dema
    return header
