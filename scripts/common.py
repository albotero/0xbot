import datetime
import time
from pandas import to_datetime
from scripts.console import C, I
from scripts.exchanges.exchange import ExchangeInterface
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


def sleep_till_next_candle(exchange: ExchangeInterface, timeframe: str, remaining: str = None) -> None:
    """Sleep until candle close time"""
    # Update console
    if remaining:
        print(C.Style(f"\r{'':<100}\r{I.CLOCK} Waiting for candle close @ {remaining} ... ", C.YELLOW), end="")
    else:
        print(C.Style(f"\r{I.CLOCK} Waiting for candle close @ timeframe {timeframe} ... ", C.YELLOW), end="")
    # Any symbol will do, in this case BTCUSDT
    close_time = exchange.get_candlestick_data(_symbol="BTCUSDT", _timeframe=timeframe, _qty=1)[0]["close_time"]
    # Get servers current time
    current_time = exchange.get_server_time()
    # Remaining ms + 1 = next open ms
    remaining_ms = close_time - current_time + 1
    remaining = ""
    step_ms = 300
    # Sleep over half a minute
    for _ in range(int(30 * 1000 / step_ms)):
        if remaining_ms > step_ms:
            remaining_ms -= step_ms
            remaining = str(datetime.timedelta(seconds=int(remaining_ms / 1000)))
            print(C.Style(f"\r{'':<100}\r{I.CLOCK} Waiting for candle close @ {remaining} ... ", C.YELLOW), end="")
            time.sleep(step_ms / 1000)
        else:
            # Clear console
            print(f"\r{'':<100}", end="\r")
            return
    # Sync again time with server after the half minute
    sleep_till_next_candle(exchange, timeframe, remaining=remaining)


def side_from_direction(direction: Direction) -> str:
    if direction == Direction.BEARISH:
        return "SELL"
    if direction == Direction.BULLISH:
        return "BUY"
