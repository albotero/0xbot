from datetime import datetime
import time
from tabulate import tabulate
from scripts.common import round_float, seconds_till_next_close
from scripts.console import C, I, progress_bar
from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Indicator, Signal, Direction
from scripts.indicators.trend.divergence import DivergenceSignal


class FuturesStrategy:
    """Open long/short positions with SL/TSL/TP

    Parameters
    ----------
    `name`: name to identify the strategy on command line

    `exchange`: exchange interface

    `signals`: list of Signal objects with the desired Indicators

    `order_value`: percentage of balance for each trade (0 to 100)

    `risk_reward_ind`: percentage for stop loss (0 to 100) or Indicator (e.g. ATR)

    `risk_reward_ratio`: reward expected for the risk

    `timeframe`: candlesticks timeframe

    `leverage`: leverage for the trades

    `min_signals_percentage`: percentage of signals to place an order

    `trailing_stop`: whether to trail or not stop loss"""

    def __init__(
        self,
        name: str,
        exchange: ExchangeInterface,
        order_value: float,
        risk_reward_ind: "float | Indicator",
        risk_reward_ratio: float,
        signals: "list[Signal | DivergenceSignal]",
        timeframe: str,
        leverage: int = 1,
        min_signals_percentage: float = 0.75,
        trailing_stop: bool = True,
    ) -> None:
        self.exchange = exchange
        self.leverage = leverage
        self.min_signals_percentage = min_signals_percentage
        self.name = name
        self.order_value = order_value
        self.risk_reward_ind = risk_reward_ind
        self.risk_reward_ratio = risk_reward_ratio
        self.signals = signals
        self.timeframe = timeframe
        self.trailing_stop = trailing_stop

    def check_signals(self) -> None:
        """Place an order if ≥ percentage of signals say so"""
        # Update console
        self.print_positions()
        # Wait for current candle to close + 3 seconds
        # Additional 3 seconds is to ensure last candle is the one that is used
        print(C.Style("{:<100}\n... idle ... ".format(""), C.YELLOW), end="")
        time.sleep(seconds_till_next_close(self.timeframe) + 3)
        # Update console
        total_symbols = len(self.exchange.symbols.keys())
        mode = "TEST" if self.exchange.test_mode else "LIVE"
        print("\r" + C.Style(f"{mode} MODE @ {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}", C.BOLD, C.PURPLE))
        # Update console
        console_data = [
            ("Strategy:", self.name),
            (" | Market:", "Futures"),
            (" @", self.timeframe),
            (" | Quote:", self.exchange.quote_asset),
            (" | Assets:", total_symbols),
            (" | Order value:", f"{self.order_value}%"),
            (" @", f"{self.leverage}x"),
        ]
        for t, d in console_data:
            print(C.Style(t, C.PURPLE, C.BOLD), C.Style(d, C.DARKCYAN), end="")
        print()
        # Update account data from Exchange
        self.exchange.update_account_data()
        # Initialize variables
        signal_weight = 1 / len(self.signals)
        # Check signals
        analyzed_index = 0
        for symbol in self.exchange.symbols.keys():
            # Only analyze if doesn't have an open position
            if self.exchange.positions.get(symbol):
                continue
            # Update price data from Exchange
            self.exchange.get_data_from_exchange(symbol=symbol, timeframe=self.timeframe)
            candles = self.exchange.candlesticks[f"{symbol}-{self.timeframe}"]
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
                analysis = C.Style("Buy/Long", C.GREEN) if avg_signal > 0 else C.Style("Sell/Short", C.RED)
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
        if self.trailing_stop:
            # Trailing stop loss callback rate
            sl = round(rr / mark_price * 100, 1)
        # Define order value
        percentage = self.order_value / 100
        val = self.exchange.account["crossWalletBalance"] * percentage * self.leverage / mark_price
        # Filter compliance
        filters = self.exchange.symbols[symbol]
        step = filters["step_size"].find("1") - 1
        val = round_float(number=val, decimal_places=step)
        val = min(max(val, filters["min_qty"]), filters["max_qty"])
        tick = filters["tick_size"].find("1") - 1
        mark_price = round_float(number=mark_price, decimal_places=tick)
        sl = round_float(number=sl, decimal_places=tick)
        tp = round_float(number=tp, decimal_places=tick)
        # Place the order
        return self.exchange.create_order(
            symbol=symbol,
            direction=direction,
            qty=val,
            price=mark_price,
            trailing_sl=self.trailing_stop,
            sl=sl,
            tp=tp,
            leverage=self.leverage,
        )

    def print_positions(self) -> None:
        """Prints a stylized summary of current open orders"""
        # Open orders
        _positions = []
        for symbol, orders in self.exchange.positions.items():
            # Only print data for open orders
            pos_amount = orders["positionAmount"]
            if not pos_amount:
                continue
            # Format data
            order_type = C.Style("Long", C.GREEN) if pos_amount > 0 else C.Style("Short", C.RED)
            amount = f"{abs(pos_amount)} {symbol.replace(self.exchange.quote_asset, '')}"
            entry = "{:.9g}".format(orders["entryPrice"])
            mark = "{:.9g}".format(orders["markPrice"])
            un_pnl = round_float(number=orders["unrealizedProfit"], decimal_places=4)
            un_pnl = C.Style(
                f"{un_pnl:+} {self.exchange.quote_asset}",
                C.RED if un_pnl < 0 else C.GREEN,
            )
            # Append to printable list
            _positions.append([C.Style(symbol, C.DARKCYAN), order_type, amount, entry, mark, un_pnl])
        # Wallet Balance
        total_balance = round_float(number=self.exchange.account["crossWalletBalance"], decimal_places=4)
        unrealized_profit = round_float(number=self.exchange.account["crossUnPnl"], decimal_places=4)
        available_balance = round_float(number=self.exchange.account["availableBalance"], decimal_places=4)
        # Clear line
        print(f"\r{'':<80}\r", end="")
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
                        " Amount",
                        " Entry price",
                        " Mark price",
                        " Unrealized PNL",
                    ],
                ),
                "\n",
            )
        print(
            f"{I.PROFIT} Total Balance:    ",
            C.Style(f"{total_balance} {self.exchange.quote_asset}", C.CYAN),
        )
        print(
            f"{I.PROFIT} Unrealized Profit:",
            C.Style(f"{unrealized_profit:+} {self.exchange.quote_asset}", C.CYAN),
        )
        print(
            f"{I.PROFIT} Available Balance:",
            C.Style(f"{available_balance} {self.exchange.quote_asset}", C.CYAN),
        )
        print()
