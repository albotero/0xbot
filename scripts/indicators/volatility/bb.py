from pandas import DataFrame
from scripts.indicators.trend.sma import sma


def bb(data: DataFrame, periods: int = 20, std_count: int = 2) -> None:
    ''' Bollinger Bands

    Return Headers: [0] Lower | [1] Middle | [2] Upper '''
    headers = [f"bbl-{periods}",
               f"bbm-{periods}",
               f"bbu-{periods}"]
    # Calculate Middle Band : SMA
    middle = data["close"].rolling(periods, min_periods=0).mean()
    # Calculate 2 Standard Deviations
    std = std_count * middle.std()
    # Calculate Lower Band : Middle Band - 2 std
    lower = middle.sub(std)
    # Calculate Upper Band : Middle Band + 2 std
    upper = middle.add(std)
    # Add data to data frame
    data[headers[0]] = lower
    data[headers[1]] = middle
    data[headers[2]] = upper
