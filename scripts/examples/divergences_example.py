from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal
from scripts.indicators.trend.divergence import DivergenceSignal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy


def strategy(exchange: ExchangeInterface, market: str) -> None:
    signals = [
        ### Check divergence between price and Stochastic Oscillator
        DivergenceSignal(
            indicator=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            indicator_header="rsi(14)",
        ),
        ### Confirm divergence with a crossover in the stochastic fast and slow lines
        ### No kwargs given => stoch uses by default periods=14 and slow_periods=3
        Signal(
            signal_ind=Indicator(Indicator.TYPE_STOCH),
            signal_header="stoch-f(14)",
            base_ind=Indicator(Indicator.TYPE_STOCH),
            base_header="stoch-s(14)",
        ),
    ]
    if market == "futures":
        strategy = FuturesStrategy(
            name="Divergence",
            exchange=exchange,
            leverage=5,
            order_value=0.5,
            signals=signals,
            timeframe="5m",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
            trailing_stop=True,
        )
        while True:
            strategy.check_signals()
    elif market == "spot":
        strategy = SpotStrategy(
            name="Divergence",
            exchange=exchange,
            order_value=2.5,
            signals=signals,
            timeframe="5m",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
        )
        while True:
            strategy.check_signals()
