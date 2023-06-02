from pandas import DataFrame


def data_to_heikin_ashi(data: DataFrame) -> None:
    """Updates open, close, high and low values from data frame"""
    # Shift data
    data["open"] = data["open"].shift(1)
    data["close"] = data["close"].shift(1)
    # Update open price: average of open and close
    data["open"] = data.loc[:, ["open", "close"]].mean(axis=1)
    # Update close price: average of open, close, high and low
    data["close"] = data.loc[:, ["open", "close", "high", "low"]].mean(axis=1)
