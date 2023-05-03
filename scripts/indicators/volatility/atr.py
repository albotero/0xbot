from pandas import DataFrame, Series


def tr(close: float, high: float, low: float) -> float:
    ''' True Range '''
    return max((high - low), abs(high - close), abs(low - close))


def atr(data: DataFrame, periods: int = 14, return_data: bool = True) -> str | Series:
    ''' Average True Range

    Return Header: ATR '''
    # Calculate TR
    _tr = data[["close", "high", "low"]].apply(lambda row: tr(*row), axis=1)
    # ATR = SMA(TR)
    atr = _tr.rolling(periods, min_periods=0).mean()
    if return_data:
        return atr
    # Modify DataFrame
    header = f"atr-{periods}"
    data[header] = atr
    return header
