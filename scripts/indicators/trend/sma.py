from pandas import DataFrame


def sma(data: DataFrame, periods: int) -> None:
    ''' Simple Moving Average

    Return Header: SMA '''
    header = f"sma-{periods}"
    data[header] = data["close"].rolling(periods, min_periods=0).mean()
    return header
