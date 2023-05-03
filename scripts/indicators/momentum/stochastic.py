from pandas import DataFrame


def stochastic(data: DataFrame, periods: int = 14, slow_periods: int = 3) -> list[str]:
    ''' Stochastic Oscilator

    Return Headers: [0] Fast Stochastic | [1] Slow Stochastic '''
    # Period's low and high
    low = data["low"].rolling(periods, min_periods=0).min()
    high = data["high"].rolling(periods, min_periods=0).max()
    headers = [f"stoch-f-{periods}",
               f"stoch-s-{periods}"]
    # Fast stochastic => (close - low) / (high - low) * 100
    data[headers[0]] = (data["close"] - low) / (high - low) * 100
    # Slow stochastic => EMA(fast_stochastic @ slow_periods)
    data[headers[1]] = data[headers[0]].ewm(
        alpha=1/slow_periods, min_periods=0, adjust=False).mean()
    return headers
