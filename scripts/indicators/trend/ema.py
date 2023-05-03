from pandas import DataFrame


def ema(data: DataFrame, periods: int) -> None:
    ''' Exponential Moving Average

    Return Header: EMA '''
    # Calculate EMA
    _ema = data["close"].ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    # Update DataFrame
    header = f"ema({periods})"
    data[header] = _ema
    return header
