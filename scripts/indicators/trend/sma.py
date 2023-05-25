from pandas import DataFrame


def sma(data: DataFrame, periods: int) -> None:
    """Simple Moving Average

    Return Header: SMA"""
    # Calculate SMA
    _sma = data["close"].rolling(periods).mean()
    # Update DataFrame
    header = f"sma({periods})"
    data[header] = _sma
    return header
