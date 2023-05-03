from pandas import DataFrame


def macd(data: DataFrame, short_term: int = 12, long_term: int = 26, signal: int = 9) -> list[str]:
    ''' Moving Average Convergence Divergence

    Return Headers: [0] MACD | [1] Signal '''
    # Calculate short-term EMA
    short_ema = data["close"].ewm(alpha=1/short_term, min_periods=0, adjust=False).mean()
    # Calculate long-term EMA
    long_ema = data["close"].ewm(alpha=1/long_term, min_periods=0, adjust=False).mean()
    # Calculate MACD by substracting long term from short term EMA
    macd = long_ema - short_ema
    headers = [f"macd-{short_term}/{long_term}",
               f"macd-s-{short_term}/{long_term}"]
    data[headers[0]] = macd
    data[headers[1]] = macd.ewm(alpha=1/signal, min_periods=0, adjust=False).mean()
    return headers
