from abc import ABCMeta, abstractmethod
from datetime import datetime
from scripts.common import round_float
from scripts.exchange import ExchangeInterface
from scripts.objects.coin import Coin
from scripts.console import *
import time


class StrategyInterface(metaclass=ABCMeta):
    name: str
    stop_loss: float

    @abstractmethod
    def determine_buy_event(self, **kwargs) -> bool: pass

    @abstractmethod
    def determine_sell_event(self, **kwargs) -> bool: pass


class Strategy:
    ''' Runs a determined strategy '''

    candle_count = 3

    def __init__(self, exchange: ExchangeInterface, strategy: StrategyInterface, timeframe: str,
                 quote_per_trade: float) -> None:
        self.exchange = exchange
        self.quote_per_trade = quote_per_trade
        self.strategy = strategy
        self.timeframe = timeframe
        self.trade_positions = {}
        print(
            "\n" + I.NOTEPAD, C.Style(" Strategy:", C.PURPLE), strategy.name,
            C.Style("- Timeframe:", C.PURPLE), timeframe,
            C.Style("- Quote per trade:", C.PURPLE), quote_per_trade, self.exchange.quote_asset)

    def analyze_symbols(self):
        ''' Analize each symbol to define trade order '''
        # Wait for current candle to close + 3 seconds
        # Additional 3 seconds is to ensure last candle is the one that is used
        print(C.Style("{:<100}\n\r... idle ... ".format(""), C.YELLOW), end="")
        time.sleep(self.seconds_till_next_close() + 3)
        # Update console
        total_symbols = len(self.exchange.symbols)
        mode = "TEST" if self.exchange.test_mode else "LIVE"
        print("\r" + C.Style(f"{mode} MODE ~ {self.strategy.name} Strategy", C.BOLD, C.PURPLE))
        print(C.Style(f"Analysis :: {total_symbols} assets @ {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                      C.DARKCYAN))
        # Iterate through the symbols
        analyzed_index = 0
        for symbol, asset in self.exchange.symbols.items():
            # Retrieve data from exchange
            candles = self.exchange.get_data_from_exchange(
                symbol=symbol, timeframe=self.timeframe, qty=self.candle_count)
            analysis = ""
            open_position = self.get_open_position(symbol)
            mark_price = candles.loc[self.candle_count - 1, "close"]
            asset.price = mark_price
            # Analyze buy if doesn't have an open position
            if not open_position and self.strategy.determine_buy_event(candles=candles):
                analysis = self.execute_buy(asset)
            # Analize sell only if has an open position
            if open_position and self.strategy.determine_sell_event(candles=candles):
                analysis = self.execute_sell(asset)
            # Update screen
            print("\r ", I.CLOCK,
                  C.Style(f"{asset.strsymbol:<12}", C.CYAN),
                  analysis if analysis else progress_bar(analyzed_index, total_symbols) + " " * 5,
                  end="")
            # Update waiting
            analyzed_index += 1
        print("\r ", I.CHECK, f"Analyzed {total_symbols} assets", " " * 80)
        self.print_positions()

    def seconds_till_next_close(self) -> int:
        ''' Calculate when the next candle will close '''
        # Calculate seconds since midnight
        now = datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = (now - midnight).total_seconds()
        # Get seconds of the timeframe
        seconds_timeframe = timeframe_to_seconds(self.timeframe)
        # Modulo = seconds since last close
        last_close = seconds_since_midnight % seconds_timeframe
        return seconds_timeframe - last_close

    def get_open_position(self, symbol) -> dict:
        ''' Returns the units in the current position for the symbol '''
        position = self.trade_positions.get(symbol)
        if position:
            # Confirm that last position hasn't been closed
            if position[-1].get("sell_price") is None:
                return position[-1]

    def execute_buy(self, asset: Coin) -> str:
        ''' Buy the asset equivalent to quote_per_trade at exchange and returns
        the result for printing '''
        try:
            # Define number of assets to buy
            amount = self.quote_per_trade / asset.price
            # Execute buy at exchange
            response = self.exchange.trade_at_market(side="BUY", asset=asset, amount=amount)
            if response.get("error"):
                raise Exception(response["error"])
            amount = float(response["amount"])
            price = float(response["price"])
            # Update trade positions
            if self.trade_positions.get(asset.symbol) is None:
                self.trade_positions[asset.symbol] = []
            self.trade_positions[asset.symbol].append({"units": amount, "buy_price": price})
            # Update message
            message = C.Style("Buy", C.GREEN) + \
                f" {amount} {asset.base} @ {round_float(number=price * amount, decimal_places=4)} {asset.quote}" + \
                " "*30 + "\n"
            return message
        except Exception as error:
            return C.Style("BUY ERROR: ", C.BOLD, C.RED) + f"{error}\n"

    def execute_sell(self, asset: Coin) -> str:
        ''' Sell all the available amount of the asset at exchange and returns
        the result for printing '''
        try:
            # Define number of assets to sell
            amount = self.trade_positions[asset.symbol][-1]["units"]
            # Execute sell at exchange
            response = self.exchange.trade_at_market(side="SELL", asset=asset, amount=amount)
            if response.get("error"):
                raise Exception(response["error"])
            amount = float(response["amount"])
            price = float(response["price"])
            # Update trade positions
            buy_price = self.trade_positions[asset.symbol][-1]["buy_price"]
            profit = (price - buy_price) * amount
            self.trade_positions[asset.symbol][-1]["sell_price"] = price
            self.trade_positions[asset.symbol][-1]["profit"] = profit
            # Update message
            message = C.Style("Sell", C.RED) + \
                f" {amount} {asset.base} @ {round_float(number=price * amount, decimal_places=4)} {asset.quote} -> " + \
                C.Style("Profit:", C.BOLD) + \
                C.Style(f" {round_float(number=profit, decimal_places=2)} {asset.quote}", C.RED if profit < 0 else C.GREEN) + \
                " "*30 + "\n"
            return message
        except Exception as error:
            return C.Style("SELL ERROR: ", C.BOLD, C.RED) + f"{error}\n"

    def print_positions(self):
        ''' Prints a stylized summary of current open orders '''
        data = []
        realized_profit = 0.0
        unrealized_profit = 0.0
        for symbol, orders in self.trade_positions.items():
            asset = self.exchange.symbols[symbol]
            for order in orders:
                realized_profit += order.get("profit", 0.0)
            last_order = orders[-1]
            if not last_order.get("sell_price"):
                unrealized_profit += last_order["units"] * (asset.price - last_order["buy_price"])
            # Only show open orders
            if last_order.get("sell_price"):
                continue
            # Get data
            entry_price = last_order["buy_price"]
            change = round_float(number=determine_percent_rise(entry_price, asset.price), decimal_places=2)
            # Append to printable list
            data.append(
                C.Style(f"{asset.strsymbol:<14}", C.DARKCYAN) +
                "|    Entry: " + C.Style(f"{round_float(entry_price, asset.precision):<13}", C.DARKCYAN) +
                "|    Mark: " + C.Style(f"{round_float(asset.price, asset.precision):<13}", C.DARKCYAN) +
                "|    " + C.Style(f"{change:+}%", C.RED if change < 0 else C.GREEN))
        # Print data
        if len(data):
            print(" ", I.TRADE, C.Style("Long Orders:  "), "{:<21}".format("\n").join(data))
        # Print profit
        unrealized_profit = round_float(number=unrealized_profit, decimal_places=4)
        realized_profit = round_float(number=realized_profit, decimal_places=4)
        print(" ", I.PROFIT, C.Style("Unrealized Profit:", C.CYAN),
              "{} {}".format(C.Style(unrealized_profit, C.RED if unrealized_profit < 0 else C.GREEN),
                             self.exchange.quote_asset))
        print(" ", I.PROFIT, C.Style("Realized Profit:", C.CYAN),
              "{} {}".format(C.Style(realized_profit, C.RED if realized_profit < 0 else C.GREEN),
                             self.exchange.quote_asset))


def determine_percent_rise(close_previous, close_current) -> float:
    ''' Calculate the percentage price rise as a float '''
    return (close_current - close_previous) * 100 / close_previous


def timeframe_to_seconds(timeframe) -> float:
    ''' Converts a timeframe string to equivalent number of seconds '''
    base = float(timeframe[:-1])
    time_unit = timeframe[-1:]
    if time_unit == "s":
        return base
    elif time_unit == "m":
        return base * 60
    elif time_unit == "h":
        return base * 60 * 60
    elif time_unit == "D":
        return base * 60 * 60 * 24
    elif time_unit == "W":
        return base * 60 * 60 * 24 * 7
    elif time_unit == "M":
        return base * 60 * 60 * 24 * 30
