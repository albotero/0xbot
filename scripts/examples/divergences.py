from scripts.indicator import Indicator, Signal
from scripts.indicators.trend.divergence import DivergenceSignal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy
from scripts.strategy import StrategyInterface


class DivergencesStrategy(StrategyInterface):
    leverage = 10
    order_value = 5
    risk_reward_ind = Indicator(Indicator.TYPE_ATR, {"periods": 14})
    risk_reward_ratio = 2
    timeframe = "15m"
    trailing_stop=True


    def strategy(self) -> None:
        signals = [
            ### Check divergence between price and RSI
            DivergenceSignal(
                indicator=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
                indicator_header="rsi(14)",
            ),
            ### RSI is < 40 or > than 60
            Signal(
                signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
                signal_header="rsi(14)",
                buy_limit=40,
                sell_limit=60,
            ),
        ]
        if self.market == "futures":
            strategy = FuturesStrategy(
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
            strategy = SpotStrategy(
                name=self.name,
                exchange=self.exchange,
                order_value=self.order_value,
                signals=signals,
                min_signals_percentage=0.75,
                timeframe=self.timeframe,
                risk_reward_ind=self.risk_reward_ind,
                risk_reward_ratio=self.risk_reward_ratio,
            )
        while True:
            strategy.check_signals()
