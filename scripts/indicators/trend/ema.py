from pandas import DataFrame


def ema(data: DataFrame, periods: int) -> None:
    ''' Exponential Moving Average

    Return Header: EMA '''
    header = f"ema-{periods}"
    data[header] = data["close"].ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    return header
