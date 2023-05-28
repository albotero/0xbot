from scripts.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.strategy import StrategyInterface


class MacdStochRsiStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "3d"
    trailing_stop = False

    def strategy(self) -> None:
        """Overrides StrategyInterface.strategy(self)"""
        signals = [
            ### MACD Histogram crosses 0
            Signal(
                signal_ind=Indicator(Indicator.TYPE_MACD),
                signal_header="macd-h(12/26/9)",
                cross_limit=0,
            ),
            ### Stoch lines diverge
            ### %K > %D: Diff > 0 => BULLISH
            ### %K < %D: Diff < 0 => BEARISH
            Signal(
                signal_ind=Indicator(Indicator.TYPE_STOCH),
                signal_header="stoch-diff(14)",
                buy_limit=0,
                sell_limit=0,
                reverse=True,
            ),
            ### RSI is > 40 for shorts or < than 60 for longs
            Signal(
                signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
                signal_header="rsi(14)",
                buy_limit=60,
                sell_limit=40,
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
