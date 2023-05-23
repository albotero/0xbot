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

    Parameters
    ----------

    `indicator_type`: constant Indicator.TYPE_...

    `timeframe`: string

    `kwargs`: optional dictionary with parameters for the specific indicator function"""

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

        Returns
        -------
        Header(s) of the resulting data in the DataFrame"""
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
        buy_limit: "float | None" = None,
        sell_limit: "float | None" = None,
        cross_limit: "float | None" = None,
        base_ind: "Indicator | None" = None,
        base_header: str = None,
        reverse: bool = False,
        rising: bool = False,
    ) -> None:
        self.signal_ind = signal_ind
        self.signal_header = signal_header
        self.base_ind = base_ind
        self.base_header = base_header
        self.buy_limit = buy_limit
        self.sell_limit = sell_limit
        self.cross_limit = cross_limit
        self.reverse = reverse
        self.rising = rising

    def emit_signal(self, data: DataFrame) -> tuple[int, str]:
        """Emit BUY, NEUTRAL or SELL signal of the indicator(s)"""
        # Update signal data
        if self.signal_header == "close":
            # Analyze base indicator
            self.base_ind.analyze_data(data)
            # Buy if price is greater than ema (trend), sell otherwise
            self.buy_limit = self.sell_limit = data.iloc[-1][self.base_header]
            # Reverse
            self.reverse = True
        else:
            self.signal_ind.analyze_data(data)
        current_signal = data.iloc[-1][self.signal_header].item()
        direction = Direction.NEUTRAL
        description = None
        # Rising
        if self.rising:
            prev_signal = data.iloc[-2][self.signal_header].item()
            if current_signal > prev_signal and not self.reverse:
                direction = Direction.BULLISH
                description = "{signal} rising".format(
                    signal=self.signal_header.replace("close", "price"),
                )
            if current_signal < prev_signal and self.reverse:
                direction = Direction.BEARISH
                description = "{signal} falling".format(
                    signal=self.signal_header.replace("close", "price"),
                )
            return direction, description
        # Buy/Sell limits
        if self.reverse:
            if self.buy_limit is not None and current_signal > self.buy_limit:
                direction = Direction.BULLISH
                description = "{signal} > {limit}".format(
                    signal=self.signal_header.replace("close", "price"),
                    limit=self.base_header if self.base_header else self.buy_limit,
                )
                return direction, description
            if self.sell_limit is not None and current_signal < self.sell_limit:
                direction = Direction.BEARISH
                description = "{signal} < {limit}".format(
                    signal=self.signal_header.replace("close", "price"),
                    limit=self.base_header if self.base_header else self.sell_limit,
                )
                return direction, description
        else:
            if self.buy_limit is not None and current_signal < self.buy_limit:
                direction = Direction.BULLISH
                description = "{signal} < {limit}".format(
                    signal=self.signal_header.replace("close", "price"),
                    limit=self.base_header if self.base_header else self.buy_limit,
                )
                return direction, description
            if self.sell_limit is not None and current_signal > self.sell_limit:
                direction = Direction.BEARISH
                description = "{signal} > {limit}".format(
                    signal=self.signal_header.replace("close", "price"),
                    limit=self.base_header if self.base_header else self.sell_limit,
                )
                return direction, description
        # Check if crosses limit
        if self.cross_limit:
            # Get last values
            last_signal = data.iloc[-2][self.signal_header].item()
            # BUY signal if crosses upwards
            if last_signal <= self.cross_limit and current_signal > self.cross_limit:
                return (
                    Direction.BEARISH if self.reverse else Direction.BULLISH,
                    f"{self.signal_header} crossed up {self.base_header}",
                )
            # SELL signal if crosses downwards
            if last_signal >= self.cross_limit and current_signal < self.cross_limit:
                return (
                    Direction.BULLISH if self.reverse else Direction.BEARISH,
                    f"{self.signal_header} crossed down {self.base_header}",
                )
        # Check if crosses base
        elif self.base_header:
            # Analyze base indicator
            self.base_ind.analyze_data(data)
            # Get last values
            last_signal = data.iloc[-2][self.signal_header].item()
            last_base = data.iloc[-2][self.base_header].item()
            current_base = data.iloc[-1][self.base_header].item()
            # BUY signal if crosses upwards
            if last_signal <= last_base and current_signal > current_base:
                return (
                    Direction.BEARISH if self.reverse else Direction.BULLISH,
                    f"{self.signal_header} crossed up {self.base_header}",
                )
            # SELL signal if crosses downwards
            if last_signal >= last_base and current_signal < current_base:
                return (
                    Direction.BULLISH if self.reverse else Direction.BEARISH,
                    f"{self.signal_header} crossed down {self.base_header}",
                )
        # NEUTRAL if no signals were emitted
        return direction, description
