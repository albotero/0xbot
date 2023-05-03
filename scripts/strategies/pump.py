from pandas import DataFrame
from scripts.strategy import determine_percent_rise, StrategyInterface


class Pump(StrategyInterface):
    ''' Pump Strategy

        When price pumps for 3 candles, buys the asset. When price drops, sells the asset '''

    name = "Pump"

    def __init__(self, candle_count: int, percentage_rise: float) -> None:
        self.candle_count = candle_count
        self.percentage_rise = percentage_rise

    def determine_buy_event(self, candles: DataFrame) -> bool:
        ''' Overrides StrategyInterface.determine_buy_event() '''
        # Determine if last values were bullish
        if all([t == "bull" for t in list(candles["trend"])]):
            perc_rise = [determine_percent_rise(candles.loc[p, "open"], candles.loc[p, "close"])
                         for p in range(self.candle_count)]
            # Buy if all last prices rose more than percentage_rise
            if all([p >= self.percentage_rise for p in perc_rise]):
                self.stop_loss = candles.loc[self.candle_count - 1, "open"]
                return True

    def determine_sell_event(self, candles: DataFrame) -> bool:
        ''' Overrides StrategyInterface.determine_sell_event() '''
        # Sell if candle closed below 50% of last candle
        prev_candle_index = self.candle_count - 2
        prev_candle_middle = (candles.loc[prev_candle_index, "open"] + candles.loc[prev_candle_index, "close"]) * .5
        curr_candle_close = candles.loc[self.candle_count - 1, "close"]
        if curr_candle_close <= prev_candle_middle:
            return True
