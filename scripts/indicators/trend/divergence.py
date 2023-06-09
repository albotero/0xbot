import numpy as np
from pandas import DataFrame, Series
from scipy.signal import argrelextrema
from scripts.indicator import Direction, Indicator


class DivergenceSignal:
    """Defines if signal is divergent from base

    Parameters
    ----------
    `indicator`: column name of the indicator

    `indicator_header`: column's indicator header for the divergence analysis

    `periods`: n of candles to analize"""

    def __init__(self, indicator: Indicator, indicator_header: str, periods: int = 50) -> None:
        self.indicator = indicator
        self.indicator_header = indicator_header
        self.price_header = "close"
        self.periods = periods

    def emit_signal(self, data: DataFrame) -> tuple[int, str]:
        # Run indicator
        self.indicator.analyze_data(data)
        # Get las n (width) rows to analyze highs and lows
        indicator_data = data.tail(n=self.periods)[self.indicator_header]
        indicator_hl = self.hl(indicator_data)
        price_data = data.tail(n=self.periods)[self.price_header]
        price_hl = self.hl(price_data)
        # Bearish divergence
        if price_hl["higher_highs"] and indicator_hl["lower_highs"]:
            return Direction.BEARISH, "Bearish divergence"
        # Bullish divergence
        if price_hl["lower_lows"] and indicator_hl["higher_lows"]:
            return Direction.BULLISH, "Bullish divergence"
        # Bearish hidden divergence
        if price_hl["lower_highs"] and indicator_hl["higher_highs"]:
            return Direction.BEARISH, "Bearish hidden divergence"
        # Bullish hidden divergence
        if price_hl["higher_lows"] and indicator_hl["lower_lows"]:
            return Direction.BULLISH, "Bullish hidden divergence"
        # No divergence found
        return Direction.NEUTRAL, ""

    def hl(self, series: Series) -> dict[str:bool]:
        """Analyze series for 2+ consecutive highs and lows

        Parameters
        ----------
        `series`: subset of data to analyze for divergences

        Returns
        -------
        >>> dict:
        {"higher_highs": bool, "higher_lows": bool, "lower_highs": bool, "lower_lows": bool}"""
        # Get highs and lows filtered by 5 periods
        array = series.to_numpy(dtype=float)
        high_indices = argrelextrema(array, np.greater, order=5)[0]
        low_indices = argrelextrema(array, np.less, order=5)[0]
        highs = [array[h] for h in high_indices]
        lows = [array[l] for l in low_indices]
        # Initialize variables
        hh = lh = hl = ll = False
        # If last value is the highest of the series, it has higher highs/lows
        # If last value is the lowest of the series, it has lower highs/lows
        if len(highs) > 1:
            hh = highs[-1] == max(highs)
            lh = highs[-1] == min(highs)
        if len(lows) > 1:
            hl = lows[-1] == max(lows)
            ll = lows[-1] == min(lows)
        # Return data
        return {
            "higher_highs": hh,
            "higher_lows": hl,
            "lower_highs": lh,
            "lower_lows": ll,
        }
