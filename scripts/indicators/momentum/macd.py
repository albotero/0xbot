from pandas import DataFrame


def macd(data: DataFrame, short_term: int = 12, long_term: int = 26, signal: int = 9) -> list[str]:
    ''' Moving Average Convergence Divergence

    Return Headers: [0] MACD | [1] Signal | [2] Histogram '''
    # Calculate short-term EMA
    short_ema = data["close"].ewm(alpha=1/short_term, min_periods=0, adjust=False).mean()
    # Calculate long-term EMA
    long_ema = data["close"].ewm(alpha=1/long_term, min_periods=0, adjust=False).mean()
    # Calculate MACD by substracting long term from short term EMA
    _macd = short_ema - long_ema
    # Calculate Signal (EMA(9) of MACD)
    signal = _macd.ewm(alpha=1/signal, min_periods=0, adjust=False).mean()
    # Update DataFrame
    headers = [f"macd({short_term}/{long_term})",
               f"macd-s({signal})",
               f"macd-h"]
    data[headers[0]] = _macd
    data[headers[1]] = signal
    data[headers[2]] = _macd - signal
    return headers
