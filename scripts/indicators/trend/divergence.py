import numpy as np
from pandas import DataFrame, Series
from scipy.signal import argrelextrema
from scripts.indicators.indicator import Direction, Indicator


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
            return Direction.BEARISH
        # Bullish divergence
        if price_hl["lower_lows"] and indicator_hl["higher_lows"]:
            return Direction.BULLISH
        # Bearish hidden divergence
        if price_hl["lower_highs"] and indicator_hl["higher_highs"]:
            return Direction.BEARISH
        # Bullish hidden divergence
        if price_hl["higher_lows"] and indicator_hl["lower_lows"]:
            return Direction.BULLISH
        # No divergence found
        return Direction.NEUTRAL

    def hl(self, series: Series) -> dir[str:bool]:
        """Analyze series for 2+ consecutive highs and lows

        Parameters
        ----------
        `series`: subset of data to analyze for divergences

        Returns
        -------
        >>> dict:
        {"higher_highs": bool, "higher_lows": bool, "lower_highs": bool, "lower_lows": bool}"""
        # Initialize variables
        hh = hl = lh = ll = True
        # Get highs filtered by 5 periods
        highs = argrelextrema(series.values, np.greater, order=5)[0]
        #
        # Iterate through highs
        # ------------------------
        # If any value is False, no need to further analysis
        for h in range(1, len(highs)):
            # If any high is lesser than the previous one, doesn't have higher highs
            if hh and highs[h] < highs[h - 1]:
                hh = False
            # In any high is greater than the previous one, doesn't have lower highs
            if lh and highs[h] > highs[h - 1]:
                lh = False
        # Get lows filtered by 5 periods
        lows = argrelextrema(series.values, np.less, order=5)[0]
        #
        # Iterate through lows.
        # ------------------------
        # If any value is False, no need to further analysis
        for l in range(1, len(lows)):
            # If any low is lesser than the previous one, doesn't have higher lows
            if hl and lows[l] < lows[l - 1]:
                hl = False
            # In any low is greater than the previous one, doesn't have lower lows
            if ll and lows[l] > lows[l - 1]:
                ll = False
        # Return data
        return {
            "higher_highs": hh,
            "higher_lows": hl,
            "lower_highs": lh,
            "lower_lows": ll,
        }
