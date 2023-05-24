import datetime
import time
from pandas import to_datetime
from scripts.console import C, I
from scripts.exchange import ExchangeInterface
from scripts.indicator import Direction


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


def sleep_till_next_candle(exchange: ExchangeInterface, timeframe: str) -> None:
    """Sleep until candle close time"""
    remaining = ""
    # Sync time with server every 5 minutes
    while True:
        # Update console
        if not remaining:
            print(C.Style(f"\r{I.CLOCK} Waiting for {timeframe} candle to close ...", C.YELLOW), end=" ")
        # Any symbol will do, in this case BTCUSDT
        close_time = exchange.get_candlestick_data(_symbol="BTCUSDT", _timeframe=timeframe, _qty=1)[0]["close_time"]
        # Get servers current time
        current_time = exchange.get_server_time()
        # Remaining ms = next close ms + 1.5 extra second to allow new candle to open
        remaining_ms = close_time - current_time + 1500
        step_ms = 330
        # Sleep over five minutes
        for _ in range(int(5 * 60 * 1000 / step_ms)):
            if remaining_ms > step_ms:
                remaining_ms -= step_ms
                remaining = str(datetime.timedelta(seconds=int(remaining_ms / 1000)))
                print(
                    C.Style(
                        f"\r{'':<100}\r{I.CLOCK} Waiting for {timeframe} candle to close @ {remaining} ...", C.YELLOW
                    ),
                    end=" ",
                )
                time.sleep(step_ms / 1000)
            else:
                # Clear console and exit iteration
                print(f"\r{'':<100}", end="\r")
                return


def side_from_direction(direction: Direction) -> str:
    if direction == Direction.BEARISH:
        return "SELL"
    if direction == Direction.BULLISH:
        return "BUY"
