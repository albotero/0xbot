from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal
from scripts.indicators.trend.divergence import DivergenceSignal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy


def strategy(exchange: ExchangeInterface, market: str) -> None:
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
    if market == "futures":
        strategy = FuturesStrategy(
            name="Divergence",
            exchange=exchange,
            leverage=5,
            order_value=3,
            signals=signals,
            timeframe="4h",
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
            min_signals_percentage=1,
            timeframe="5m",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
        )
        while True:
            strategy.check_signals()
