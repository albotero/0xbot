from scripts.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.strategy import StrategyInterface


class StochasticMaStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "15m"
    trailing_stop = True

    def strategy(self) -> None:
        """Overrides StrategyInterface.strategy(self)"""
        stoch_indicator = Indicator(Indicator.TYPE_STOCH)
        signals = [
            ### K is greater or lower than D
            ### K > D: Diff > 0 => BULLISH
            ### K < D: Diff < 0 => BEARISH
            Signal(
                signal_ind=stoch_indicator,
                signal_header="stoch-diff(14)",
                buy_limit=0,
                sell_limit=0,
                reverse=True,
            ),
            ### K is < 40 for longs and > 60 for shorts
            Signal(
                signal_ind=stoch_indicator,
                signal_header="stoch-k(14)",
                buy_limit=40,
                sell_limit=60,
            ),
            ### Only place trades with the trend
            Signal(
                signal_ind=None,
                signal_header="close",
                base_ind=Indicator(Indicator.TYPE_EMA, {"periods": 50}),
                base_header="ema(50)",
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
