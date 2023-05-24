from pandas import DataFrame


def macd(data: DataFrame, short_term: int = 12, long_term: int = 26, signal: int = 9) -> list[str]:
    """Moving Average Convergence Divergence

    Return Headers: [0] MACD | [1] Signal | [2] Histogram | [3] Histogram's Moving Average for signal periods"""
    # Calculate short-term EMA
    short_ema = data["close"].ewm(alpha=1 / short_term, min_periods=0, adjust=False).mean()
    # Calculate long-term EMA
    long_ema = data["close"].ewm(alpha=1 / long_term, min_periods=0, adjust=False).mean()
    # Calculate MACD by substracting long term from short term EMA
    macd_line = short_ema - long_ema
    # Calculate Signal (EMA(9) of MACD)
    signal_line = macd_line.ewm(alpha=1 / signal, min_periods=0, adjust=False).mean()
    # Update DataFrame
    headers = [
        f"macd({short_term}/{long_term})",
        f"macd-s({short_term}/{long_term}/{signal})",
        f"macd-h({short_term}/{long_term}/{signal})",
        f"macd-ma({short_term}/{long_term}/{signal})",
    ]
    data[headers[0]] = macd_line
    data[headers[1]] = signal_line
    data[headers[2]] = macd_line - signal
    data[headers[3]] = data[headers[2]].rolling(signal, min_periods=0).mean()
    return headers
