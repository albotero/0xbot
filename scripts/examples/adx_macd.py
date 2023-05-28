from scripts.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.strategy import StrategyInterface


class AdxMacdStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "2h"
    trailing_stop = True

    def strategy(self) -> None:
        """Overrides StrategyInterface.strategy(self)"""
        signals = [
            ### MACD Histogram crosses 0
            Signal(
                signal_ind=Indicator(Indicator.TYPE_MACD),
                signal_header="macd-h(12/26/9)",
                cross_limit=0,
            ),
            ### D+ is greater or lower than D-
            ### D+ > D-: Diff > 0 => BULLISH
            ### D+ < D-: Diff < 0 => BEARISH
            ### Only trade if there is a trend: ADX > 20
            Signal(
                signal_ind=Indicator(Indicator.TYPE_ADX),
                signal_header="adx-diff(14)",
                buy_limit=0,
                sell_limit=0,
                reverse=True,
                consolidation_header="adx(14)",
                consolidation_limit=20,
            ),
        ]
        if self.market == "futures":
            ta = FuturesStrategy(
                name=self.name,
                exchange=self.exchange,
                leverage=self.leverage,
                order_value=self.order_value,
                signals=signals,
                timeframe=self.timeframe,
                risk_reward_ind=self.risk_reward_ind,
                risk_reward_ratio=self.risk_reward_ratio,
                trailing_stop=self.trailing_stop,
            )
        while True:
            ta.check_signals()
