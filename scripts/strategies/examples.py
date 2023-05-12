from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal
from scripts.indicators.trend.divergence import DivergenceSignal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy


def example_divergences(exchange: ExchangeInterface, market: str) -> None:
    signals = [
        # Check divergence between price and Stochastic Oscillator
        DivergenceSignal(
            indicator=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            indicator_header="rsi(14)",
        ),
        # Confirm divergence with a crossover in the stochastic fast and slow lines
        # No kwargs given => stoch uses by default periods=14 and slow_periods=3
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
            order_value=10,
            signals=signals,
            timeframe="2h",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
            trailing_stop=True,
        )
        while True:
            strategy.check_signals()


def example_technical_analysis(exchange: ExchangeInterface, market: str) -> None:
    signals = [
        # Price is above/below DEMA to confirm trend
        Signal(
            signal_ind=None,
            signal_header="close",
            base_ind=Indicator(Indicator.TYPE_DEMA, {"periods": 20}),
            base_header="dema(20)",
        ),
        # RSI is < or > than 50
        Signal(
            signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            signal_header="rsi(14)",
            buy_limit=50,
            sell_limit=50,
        ),
        # RSI crosses EMA(RSI)
        Signal(
            signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            signal_header="rsi(14)",
            base_ind=Indicator(Indicator.TYPE_EMA, {"periods": 14, "header": "rsi(14)"}),
            base_header="ema-rsi(14)",
        ),
    ]
    if market == "futures":
        ta = FuturesStrategy(
            name="Technical Analysis",
            exchange=exchange,
            leverage=5,
            order_value=10,
            signals=signals,
            timeframe="2h",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
            trailing_stop=True,
        )
    elif market == "spot":
        ta = SpotStrategy(
            name="Technical Analysis",
            exchange=exchange,
            order_value=5,
            signals=signals,
            timeframe="15m",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
        )
    while True:
        ta.check_signals()
