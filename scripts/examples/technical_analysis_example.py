from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy


def strategy(exchange: ExchangeInterface, market: str) -> None:
    signals = [
        ### Price is above/below DEMA to confirm trend
        Signal(
            signal_ind=None,
            signal_header="close",
            base_ind=Indicator(Indicator.TYPE_DEMA, {"periods": 20}),
            base_header="dema(20)",
        ),
        ### RSI crosses EMA(RSI)
         Signal(
            signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
            signal_header="rsi(14)",
            base_ind=Indicator(Indicator.TYPE_EMA, {"periods": 14, "header": "rsi(14)"}),
            base_header="ema-rsi(14)",
         ),
        ### RSI is < 30 or > 70
        Signal(
           signal_ind=Indicator(Indicator.TYPE_RSI, {"periods": 14}),
           signal_header="rsi(14)",
           buy_limit=30,
           sell_limit=70,
        ),
    ]
    if market == "futures":
        ta = FuturesStrategy(
            name="Technical Analysis",
            exchange=exchange,
            leverage=5,
            order_value=3,
            signals=signals,
            timeframe="4h",
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
