from datetime import datetime
from pandas import to_datetime

from scripts.indicators.indicator import Direction


def readable_time(time):
    return to_datetime(time, unit="ms", utc=True).map(lambda x: x.tz_convert("America/Bogota"))


def round_float_to_str(number: float, decimal_places: int, signed: bool = False) -> str:
    """Rounds a float number to a string with desired decimal places"""
    return f"{number:+.{decimal_places}f}" if signed else f"{number:.{decimal_places}f}"


def str_to_decimal_places(value: str) -> int:
    """Gets number of decimal places from a string number"""
    values = value.split(".")
    if len(values) == 2:
        # Has decimal places
        return values[1].find("1") + 1
    else:
        # It's an integer!
        return 0


def determine_percent_rise(open: float, close: float) -> float:
    """Calculate the percentage price rise as a float"""
    return (close - open) * 100 / open


def timeframe_to_seconds(timeframe: str) -> float:
    """Converts a timeframe string to equivalent number of seconds"""
    base = float(timeframe[:-1])
    time_unit = timeframe[-1:]
    if time_unit == "s":
        return base
    elif time_unit == "m":
        return base * 60
    elif time_unit == "h":
        return base * 60 * 60
    elif time_unit == "d":
        return base * 60 * 60 * 24
    elif time_unit == "w":
        return base * 60 * 60 * 24 * 7
    elif time_unit == "M":
        return base * 60 * 60 * 24 * 30


def seconds_till_next_close(timeframe: str) -> int:
    """Calculate when the next candle will close"""
    # Calculate seconds since midnight
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    # Get seconds of the timeframe
    seconds_timeframe = timeframe_to_seconds(timeframe)
    # Modulo = seconds since last close
    last_close = seconds_since_midnight % seconds_timeframe
    return seconds_timeframe - last_close


def side_from_direction(direction: Direction) -> str:
    if direction == Direction.BEARISH:
        return "SELL"
    if direction == Direction.BULLISH:
        return "BUY"
