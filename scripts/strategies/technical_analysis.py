from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal
from scripts.markets.futures import FuturesStrategy
from scripts.markets.spot import SpotStrategy


def technical_analysis(exchange: ExchangeInterface, market: str) -> "FuturesStrategy | SpotStrategy":
    """Define a Strategy"""
    signals = [
        # Price is above/below long-term DEMA to confirm trend
        Signal(
            signal_ind=None,
            signal_header="close",
            base_ind=Indicator(Indicator.TYPE_DEMA, {"periods": 50}),
            base_header="dema(50)",
        ),
        # MACD line is above/below 0
        Signal(
            signal_ind=Indicator(Indicator.TYPE_MACD),
            signal_header="macd(12/26)",
            buy_limit=0.0,
            sell_limit=0.0,
            reverse=True,
        ),
        # MACD Signal line crosses 0
        Signal(
            signal_ind=Indicator(Indicator.TYPE_MACD),
            signal_header="macd-s(9)",
            base_ind=0.0,
            base_header="zero",
        ),
        # MACD Hystogram is above/below 0
        Signal(
            signal_ind=Indicator(Indicator.TYPE_MACD),
            signal_header="macd-h(12/26/9)",
            buy_limit=0.0,
            sell_limit=0.0,
            reverse=True,
        ),
        # RSI in oversold/overbougth range
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
            order_value=1,
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
            order_value=2,
            signals=signals,
            timeframe="1m",
            risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
            risk_reward_ratio=3,
        )
    while True:
        ta.check_signals()
