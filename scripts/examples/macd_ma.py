from scripts.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.strategy import StrategyInterface


class MacdMaStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "15m"
    trailing_stop=False


    def strategy(self) -> None:
        """Overrides StrategyInterface.strategy(self)"""
        signals = [
            ### MACD Histogram crosses 0
            Signal(
                signal_ind=Indicator(Indicator.TYPE_MACD),
                signal_header="macd-h(12/26/9)",
                cross_limit=0,
            ),
            ### Only place trades with the trend
            Signal(
                signal_ind=None,
                signal_header="close",
                base_ind=Indicator(Indicator.TYPE_EMA, {"periods": 20}),
                base_header="ema(20)",
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