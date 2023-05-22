from scripts.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy
from scripts.strategy import StrategyInterface


class MacdRsiStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "1d"
    trailing_stop=True


    def strategy(self) -> None:
        signals = [
            ### Price is above/below DEMA to confirm trend
            Signal(
                signal_ind=None,
                signal_header="close",
                base_ind=Indicator(Indicator.TYPE_DEMA, {"periods": 20}),
                base_header="dema(20)",
            ),
            ### MACD Histogram crosses 0
            Signal(
                signal_ind=Indicator(Indicator.TYPE_MACD),
                signal_header="macd-h(12/26/9)",
                cross_limit=0,
            ),
            ### Confirm momentum with RSI
            Signal(
            signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            signal_header="rsi(14)",
            buy_limit=40,
            sell_limit=60,
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
        elif self.market == "spot":
            ta = SpotStrategy(
                name=self.name,
                exchange=self.exchange,
                order_value=self.order_value,
                signals=signals,
                timeframe=self.timeframe,
                risk_reward_ind=self.risk_reward_ind,
                risk_reward_ratio=self.risk_reward_ratio,
            )
        while True:
            ta.check_signals()
