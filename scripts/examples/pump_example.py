from pandas import DataFrame
from scripts.markets import spot


class Pump(spot.StrategyInterface):
    """Pump Strategy

    When price pumps for 3 candles, buys the asset. When price drops, sells the asset"""

    name = "Pump"

    def __init__(self, candle_count: int, percentage_rise: float) -> None:
        self.candle_count = candle_count
        self.percentage_rise = percentage_rise

    def determine_buy_event(self, candles: DataFrame) -> bool:
        """Overrides StrategyInterface.determine_buy_event()"""
        # Determine if last values rose at least percentage_rise
        bullish = (
            candles[["open", "close"]]
            .tail(self.candle_count)
            .apply(lambda row: spot.determine_percent_rise(row["open"], row["close"]) >= self.percentage_rise, axis=1)
        )
        return bullish.all()

    def determine_sell_event(self, candles: DataFrame) -> bool:
        """Overrides StrategyInterface.determine_sell_event()"""
        # Sell if candle closed below 50% of last candle
        # prev_candle_middle = candles[["open", "close"]].shift(1).mean(axis=1)
        # Sell if candle closed below last candle's close
        signal = candles["close"] - candles["close"].shift(1)
        return signal.tail(1).item() <= 0
