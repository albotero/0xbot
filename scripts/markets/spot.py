from datetime import datetime
from tabulate import tabulate
from scripts.common import round_float_to_str, sleep_till_next_candle
from scripts.console import *
from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Direction, Indicator, Signal
from scripts.indicators.trend.divergence import DivergenceSignal


class SpotStrategy:
    """Open long/short positions with SL/TP

    Parameters
    ----------
    `name`: name to identify the strategy on command line

    `exchange`: exchange interface

    `signals`: list of Signal objects with the desired Indicators

    `order_value`: percentage of balance for each trade (0 to 100)

    `risk_reward_ind`: percentage for stop loss (0 to 100) or Indicator (e.g. ATR)

    `risk_reward_ratio`: reward expected for the risk

    `timeframe`: candlesticks timeframe

    `min_signals_percentage`: percentage of signals to place an order"""

    def __init__(
        self,
        name: str,
        exchange: ExchangeInterface,
        order_value: float,
        risk_reward_ind: "float | Indicator",
        risk_reward_ratio: float,
        signals: "list[Signal | DivergenceSignal]",
        timeframe: str,
        min_signals_percentage: float = 0.75,
    ) -> None:
        self.exchange = exchange
        self.min_signals_percentage = min_signals_percentage
        self.name = name
        self.order_value = order_value
        self.risk_reward_ind = risk_reward_ind
        self.risk_reward_ratio = risk_reward_ratio
        self.signals = signals
        self.timeframe = timeframe

    def check_signals(self) -> None:
        """Place an order if ≥ percentage of signals say so"""
        # Update console
        self.print_positions()
        # Sleep till candle close
        sleep_till_next_candle(exchange=self.exchange, timeframe=self.timeframe)
        # Update console
        total_symbols = len(self.exchange.symbols.keys())
        mode = "TEST" if self.exchange.test_mode else "LIVE"
        print("\r" + C.Style(f"{mode} MODE @ {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}", C.BOLD, C.PURPLE))
        # Update console
        console_data = [
            ("Strategy:", self.name),
            (" | Market:", "Spot"),
            (" @", self.timeframe),
            (" | Quote:", self.exchange.quote_asset),
            (" | Assets:", total_symbols),
            (" | Order value:", f"{self.order_value}%"),
        ]
        for t, d in console_data:
            print(C.Style(t, C.PURPLE, C.BOLD), C.Style(d, C.DARKCYAN), end="")
        print()
        # Update account data from Exchange
        self.exchange.update_account_data()
        # Get servers current time
        current_time = self.exchange.get_server_time()
        # Initialize variables
        signal_weight = 1 / len(self.signals)
        # Check signals
        analyzed_index = 0
        for symbol, symbol_data in self.exchange.symbols.items():
            # Only analyze if doesn't have an open position
            if self.exchange.balance.get(symbol_data["base"]):
                continue
            # Update price data from Exchange
            self.exchange.get_data_from_exchange(symbol=symbol, timeframe=self.timeframe)
            # Get closed candles
            candles = self.exchange.candlesticks[f"{symbol}-{self.timeframe}"]
            candles = candles.loc[candles["close_time"] <= current_time]
            avg_signal = 0
            analysis = None
            descriptions = []
            for signal in self.signals:
                # Direction => BULLISH (+1) for BUY signal | 0 for NEUTRAL | BEARISH (-1) for SELL signal
                direction, desc = signal.emit_signal(data=candles)
                avg_signal += direction * signal_weight
                if desc:
                    descriptions.append(desc)
            # Define if needs to place an order
            if abs(avg_signal) >= self.min_signals_percentage:
                analysis = C.Style("Buy", C.GREEN) if avg_signal > 0 else C.Style("Sell", C.RED)
                analysis += "\n    " + self.place_order(
                    symbol=symbol,
                    mark_price=candles.iloc[-1]["close"].item(),
                    direction=Direction.BULLISH if avg_signal > 0 else Direction.BEARISH,
                )
            else:
                # Reset descriptions
                descriptions = []
            # Update screen
            descriptions = C.Style(" ** ", C.DARKCYAN).join(descriptions)
            if analysis:
                analysis = "{}  {}  {:<30}\n".format(descriptions, C.Style("=>", C.DARKCYAN), analysis)
                print(
                    "\r ",
                    I.CLOCK,
                    C.Style(f"{symbol} ::", C.CYAN),
                    f"{analysis:<50}",
                    end="",
                )
            else:
                print(
                    "\r ",
                    I.CLOCK,
                    C.Style(f"{symbol:<20}", C.CYAN),
                    "{:<50}".format(progress_bar(analyzed_index, total_symbols)),
                    end="",
                )
            # Update waiting
            analyzed_index += 1
        # Update account data from Exchange
        print()
        self.exchange.update_account_data()

    def place_order(self, symbol: str, mark_price: float, direction: int) -> str:
        """Places an order on the exchange"""
        # Define RR Range
        rr = 0.0
        if type(self.risk_reward_ind) == Indicator:
            # ATR
            candles = self.exchange.candlesticks[f"{symbol}-{self.timeframe}"]
            self.risk_reward_ind.analyze_data(candles)
            rr = candles.iloc[-1]["atr({})".format(self.risk_reward_ind.function_kwargs["periods"])]
        else:
            # Risk Reward Indicator is a float with % of RR
            rr = mark_price * self.risk_reward_ind / 100
        # Define TP/SL
        tp = mark_price + rr * self.risk_reward_ratio * direction
        sl = mark_price - rr * direction
        # Define order value
        percentage = self.order_value / 100
        val = self.calc_total_wallet_balance() * percentage / mark_price
        # Place the order
        return self.exchange.create_order(
            symbol=symbol,
            direction=direction,
            qty=val,
            price=mark_price,
            sl=sl,
            tp=tp,
        )

    def calc_total_wallet_balance(self, asset: str = None, balance_type: str = None) -> float:
        """Returns balances equivalent in quote asset"""
        # Initialize variables
        free = 0.0
        locked = 0.0
        if asset:
            # Balance of a single asset
            bal = self.exchange.balance[asset]
            free += bal["free"] * pos["markPrice"]
            locked += bal["locked"] * pos["markPrice"]
        else:
            # Total wallet balance
            for a, pos in self.exchange.balance.items():
                free += pos["free"] * pos["markPrice"]
                locked += pos["locked"] * pos["markPrice"]
        # Return balance
        if balance_type == "free":
            return free
        if balance_type == "locked":
            return locked
        return free + locked

    def print_positions(self) -> None:
        """Prints a stylized summary of current open orders"""
        # Open orders
        _positions = []
        unrealized_profit = 0.0
        for symbol, position in self.exchange.positions.items():
            asset = symbol.replace(self.exchange.quote_asset, "")
            # Only print data for open orders
            pos_amount = position["positionAmount"]
            if not pos_amount:
                continue
            # Format data
            side = C.Style(position["side"], C.GREEN if position["side"] == "BUY" else C.RED)
            amount = f"{abs(pos_amount)} {asset}"
            entry = "{:.9g}".format(position["entryPrice"])
            entry_value = abs(pos_amount) * position["entryPrice"]
            entry_value = f"{round_float_to_str(number=entry_value, decimal_places=4)} {self.exchange.quote_asset}"
            mark = "{:.9g}".format(position["markPrice"])
            mark_value = abs(pos_amount) * position["markPrice"]
            mark_value = f"{round_float_to_str(number=mark_value, decimal_places=4)} {self.exchange.quote_asset}"
            un_pnl = position["unrealizedProfit"]
            unrealized_profit += un_pnl
            un_pnl = C.Style(
                f"{round_float_to_str(number=un_pnl,decimal_places=4,signed=True):>10} {self.exchange.quote_asset}",
                C.RED if un_pnl < 0 else C.GREEN,
            )
            # Append to printable list
            _positions.append(
                [
                    C.Style(symbol, C.DARKCYAN),
                    side,
                    position["type"],
                    amount,
                    entry,
                    entry_value,
                    mark,
                    mark_value,
                    un_pnl,
                ]
            )
        # Wallet Balance
        total_balance = round_float_to_str(number=self.calc_total_wallet_balance(), decimal_places=4)
        locked_balance = round_float_to_str(
            number=self.calc_total_wallet_balance(balance_type="locked"), decimal_places=4
        )
        free_balance = round_float_to_str(number=self.calc_total_wallet_balance(balance_type="free"), decimal_places=4)
        unrealized_profit = C.Style(
            f"{round_float_to_str(number=unrealized_profit,decimal_places=4,signed=True)} {self.exchange.quote_asset}",
            C.RED if unrealized_profit < 0 else C.GREEN,
        )
        # Clear line
        print(f"\r{'':<80}", end="\r")
        # Print data
        if len(_positions):
            print(
                "\n",
                tabulate(
                    _positions,
                    numalign="left",
                    stralign="left",
                    headers=[
                        " Symbol",
                        " Side",
                        " Type",
                        " Amount",
                        " Entry price",
                        " Mark price",
                        " Unrealized PNL",
                    ],
                ),
                "\n",
            )
        print(
            f"{I.PROFIT} Unrealized Profit:",
            C.Style(unrealized_profit, C.CYAN),
        )
        print(
            f"{I.PROFIT} Locked {self.exchange.quote_asset} Equivalent Balance:",
            C.Style(f"{locked_balance} {self.exchange.quote_asset}", C.CYAN),
        )
        print(
            f"{I.PROFIT} Free {self.exchange.quote_asset} Equivalent Balance:  ",
            C.Style(f"{free_balance} {self.exchange.quote_asset}", C.CYAN),
        )
        print(
            f"{I.PROFIT} Total {self.exchange.quote_asset} Equivalent Balance: ",
            C.Style(f"{total_balance} {self.exchange.quote_asset}", C.CYAN),
        )
        print()
