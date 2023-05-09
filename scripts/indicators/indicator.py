from pandas import DataFrame
from scripts.indicators.momentum.macd import macd
from scripts.indicators.momentum.rsi import rsi
from scripts.indicators.momentum.stochastic import stochastic
from scripts.indicators.trend.adx import adx
from scripts.indicators.trend.dema import dema
from scripts.indicators.trend.ema import ema
from scripts.indicators.trend.sma import sma
from scripts.indicators.volatility.atr import atr
from scripts.indicators.volatility.bb import bb


class Direction:
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1


class Indicator:
    """Defines which function to use to analyze data

    :parameter indicator_type: constant Indicator.TYPE_...
    :parameter timeframe: string
    :parameter kwargs: optional dictionary with parameters for the specific indicator function"""

    TYPE_MACD = "MACD"
    TYPE_RSI = "RSI"
    TYPE_STOCH = "Stochastic Oscillator"
    TYPE_ADX = "ADX"
    TYPE_DEMA = "Double EMA"
    TYPE_EMA = "EMA"
    TYPE_SMA = "SMA"
    TYPE_ATR = "ATR"
    TYPE_BB = "Bollinger Bands"

    functions = {
        TYPE_MACD: macd,
        TYPE_RSI: rsi,
        TYPE_STOCH: stochastic,
        TYPE_ADX: adx,
        TYPE_DEMA: dema,
        TYPE_EMA: ema,
        TYPE_SMA: sma,
        TYPE_ATR: atr,
        TYPE_BB: bb,
    }

    def __init__(self, indicator_type: str, kwargs: dict[str, "int | bool"] = None) -> None:
        self.indicator_type = indicator_type
        self.function_kwargs = kwargs

    def analyze_data(self, data: DataFrame) -> "str | list[str]":
        """Execute analysis funciton

        Returns header(s) of the resulting data in the DataFrame"""
        f = self.functions[self.indicator_type]
        if self.function_kwargs:
            return f(data, **self.function_kwargs)
        return f(data)


class Signal:
    """Checks indicator data to emit a signal

    Limits are relative if base indicator is provided, else are absolute

    If limits are not provided, cross signal is used

    For mark price, provide signal_header without signal_ind"""

    def __init__(
        self,
        *,
        signal_ind: "Indicator | None",
        signal_header: str,
        buy_limit: float = 0.0,
        sell_limit: float = 0.0,
        base_ind: "Indicator | float | None" = None,
        base_header: str = None,
        reverse: bool = False,
    ) -> None:
        self.signal_ind = signal_ind
        self.signal_header = signal_header
        self.base_ind = base_ind
        self.base_header = base_header
        self.buy_limit = buy_limit
        self.sell_limit = sell_limit
        self.reverse = reverse

    def emit_signal(self, data: DataFrame) -> tuple[int, str]:
        """Emit BUY, NEUTRAL or SELL signal of the indicator(s)"""
        # If signal is the price
        signal_price = self.signal_header == "close"
        # Update signal data
        if signal_price:
            self.buy_limit = self.sell_limit = data.iloc[-1]["close"]
        else:
            self.signal_ind.analyze_data(data)
        current_signal = data.iloc[-1][self.signal_header].item()
        # Buy/Sell limits
        direction = Direction.NEUTRAL
        if self.reverse:
            if self.buy_limit and current_signal >= self.buy_limit:
                direction = Direction.BULLISH
            if self.sell_limit and current_signal <= self.sell_limit:
                direction = Direction.BEARISH
        else:
            if self.buy_limit and current_signal <= self.buy_limit:
                direction = Direction.BULLISH
            if self.sell_limit and current_signal >= self.sell_limit:
                direction = Direction.BEARISH
        if direction != Direction.NEUTRAL:
            return (
                direction,
                "{signal} ≤ {limit}".format(
                    signal=self.signal_header.replace("close", "price"),
                    limit=self.base_header if self.base_header else self.buy_limit,
                ),
            )
        # Check if crosses base
        if self.base_header:
            if type(self.base_ind) == float:
                # Check if crosses a threshold
                # Get last values
                last_signal = data.iloc[-2][self.signal_header].item()
                # BUY signal if crosses upwards
                if last_signal <= self.base_ind and current_signal > self.base_ind:
                    return Direction.BULLISH, f"{self.signal_header} crossed up {self.base_header}"
                # SELL signal if crosses downwards
                if last_signal >= self.base_ind and current_signal < self.base_ind:
                    return Direction.BEARISH, f"{self.signal_header} crossed down {self.base_header}"
            else:
                # Check if crosses base indicator
                # Analyze base indicator
                self.base_ind.analyze_data(data)
                # Get last values
                last_signal = data.iloc[-2][self.signal_header].item()
                last_base = data.iloc[-2][self.base_header].item()
                current_base = data.iloc[-1][self.base_header].item()
                # BUY signal if crosses upwards
                if last_signal <= last_base and current_signal > current_base:
                    return Direction.BULLISH, f"{self.signal_header} crossed up {self.base_header}"
                # SELL signal if crosses downwards
                if last_signal >= last_base and current_signal < current_base:
                    return Direction.BEARISH, f"{self.signal_header} crossed down {self.base_header}"
        # NEUTRAL if no signals were emitted
        return Direction.NEUTRAL, None
