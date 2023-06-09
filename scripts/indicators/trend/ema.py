from pandas import DataFrame


def ema(data: DataFrame, periods: int, header: str = "close") -> None:
    """Exponential Moving Average

    Return Header: EMA"""
    # Calculate EMA
    _ema = data[header].ewm(span=periods, adjust=False).mean()
    # Update DataFrame
    header = f"ema({periods})" if header == "close" else f"ema-{header}"
    data[header] = _ema
    return header
