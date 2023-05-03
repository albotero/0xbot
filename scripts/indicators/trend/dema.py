from pandas import DataFrame


def dema(data: DataFrame, periods: int) -> str:
    ''' Double Exponential Moving Average

    Return Header: DEMA '''
    # Calculate EMA from the data
    ema = data["close"].ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    #  Calculate EMA from the previous calculated EMA
    header = f"dema-{periods}"
    data[header] = ema.ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    return header
