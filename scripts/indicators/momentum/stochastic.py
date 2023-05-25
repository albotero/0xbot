from pandas import DataFrame


def stochastic(data: DataFrame, periods: int = 14, slow_periods: int = 3) -> list[str]:
    """Stochastic Oscilator

    Return Headers: [0] Fast Stochastic (K) | [1] Slow Stochastic (D) | [2] K-D Diff"""
    # Period's low and high
    low = data["low"].rolling(periods).min()
    high = data["high"].rolling(periods).max()
    # Fast stochastic => (close - low) / (high - low) * 100
    fast = (data["close"] - low) / (high - low) * 100
    # Slow stochastic => EMA(fast_stochastic @ slow_periods)
    slow = fast.ewm(span=slow_periods, adjust=False).mean()
    # Update DataFrame
    headers = [
        f"stoch-k({periods})",
        f"stoch-d({periods})",
        f"stoch-diff({periods})",
    ]
    data[headers[0]] = fast
    data[headers[1]] = slow
    data[headers[2]] = fast - slow
    return headers
