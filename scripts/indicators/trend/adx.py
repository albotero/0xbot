from pandas import DataFrame
from scripts.indicators.volatility.atr import atr


def adx(data: DataFrame, periods: int = 14) -> list[str]:
    ''' Average Directional Index

    Return Headers: [0] -DI | [1] ADX | [2] +DI '''
    # +DM = max(current_high - previous_high, 0)
    # -DM = max(previous_low - current_low, 0)
    plus_dm = (data["high"] - data["high"].shift(1)).clip(lower=0)
    minus_dm = (data["low"].shift(1) - data["low"]).clip(lower=0)
    # Smooth DM with EMA
    ema_plus_dm = plus_dm.ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    ema_minus_dm = minus_dm.ewm(alpha=1/periods, min_periods=0, adjust=False).mean()
    # Calculate ATR
    _atr = atr(data=data, periods=periods, return_data=True)
    # DI = 100 * [ EMA (DM) / ATR ]
    plus_di = (ema_plus_dm / _atr).mul(100)
    minus_di = (ema_minus_dm / _atr).mul(100)
    # DI = | +DI - -DI | / | +DI + -DI |  * 100
    di = ((plus_di - minus_di).abs() / (plus_di + minus_di).abs()).mul(100)
    # ADX = SMA(TR)
    adx = di.rolling(periods, min_periods=0).mean()
    # Add data to dataframe
    headers = [f"-di-{periods}",
               f"adx-{periods}",
               f"+di-{periods}"]
    data[headers[0]] = minus_di
    data[headers[1]] = adx
    data[headers[2]] = plus_di
    return headers
