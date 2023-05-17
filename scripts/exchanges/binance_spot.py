from binance.error import ClientError
from binance.spot import Spot
from pandas import DataFrame
from scripts.common import readable_time, round_float_to_str, side_from_direction, str_to_decimal_places
from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Direction
from scripts.console import C, I


class BinanceSpot(ExchangeInterface):
    candlesticks: dict[str, DataFrame] = {}
    positions: dict[str, dict[str, str]] = {}

    def __init__(self, test_mode: bool, api_key: str, secret_key: str, quote_asset: str, candle_count: int = 200):
        try:
            params = {"key": api_key, "secret": secret_key}
            if test_mode:
                params["base_url"] = "https://testnet.binance.vision"
            self.client = Spot(**params)
            print(I.CHECK, "Successful connection to account")
            self.account = {}
            self.balance = None
            self.candle_count = candle_count
            self.quote_asset = quote_asset
            self.test_mode = test_mode
            self.query_quote_asset_list()
            self.update_account_data()
            self.maker_fee = float(self.account["commissionRates"]["maker"])
            self.taker_fee = float(self.account["commissionRates"]["taker"])
            print(
                I.WARNING,
                C.Style("Commissions:", C.YELLOW),
                f"maker {self.maker_fee * 100:.3f}% | taker {self.taker_fee * 100:.3f}%",
            )
        except Exception as ex:
            print(C.Style(I.CROSS + " Error @ binance_conn.get_account ::", C.BOLD, C.RED), ex)

    def query_quote_asset_list(self) -> None:
        """Retrieve quotes of crypto against Quote"""
        # Update console
        print(C.Style(f"{I.CLOCK} Receiving assets data ... ", C.DARKCYAN), end="")
        # Retrieve data
        symbol_dictionary = self.client.exchange_info()
        # Convert into a dataframe
        symbol_dataframe = DataFrame(symbol_dictionary["symbols"])
        # Extract only those symbols with a base asset of Quote and status of TRADING
        quote_symbol_dataframe = symbol_dataframe.loc[symbol_dataframe["quoteAsset"] == self.quote_asset]
        quote_symbol_dataframe = quote_symbol_dataframe.loc[quote_symbol_dataframe["status"] == "TRADING"]
        # Update console
        print(f"\r{I.CHECK} Received list of {len(quote_symbol_dataframe)} assets{'':<10}")
        # Return list
        symbols = {}
        for _, row in quote_symbol_dataframe.iterrows():
            data = {
                "base": row["baseAsset"],
                "quote": row["quoteAsset"],
            }
            for filter in row["filters"]:
                # Market trades need to fill both LOT_SIZE and MARKET_LOT_SIZE
                if filter["filterType"] == "PRICE_FILTER":
                    data["tick_size"] = filter["tickSize"]
                elif filter["filterType"] == "LOT_SIZE":
                    data["min_qty"] = filter["minQty"]
                    data["max_qty"] = filter["maxQty"]
                    data["step_size"] = filter["stepSize"]
                elif filter["filterType"] == "MARKET_LOT_SIZE":
                    data["min_qty"] = max(data["min_qty"], filter["minQty"])
                    data["max_qty"] = min(data["max_qty"], filter["maxQty"])
                    data["step_size"] = max(filter["stepSize"], data["step_size"])
            symbols[row["symbol"]] = data
        self.symbols = symbols

    def update_account_data(self) -> None:
        """Retrieves updated data from Binance Futures account"""
        # Update console
        print(C.Style(f"\r{I.CLOCK} Updating account data ... ", C.DARKCYAN), end=" " * 50)
        # Update account
        self.account = self.client.account()
        # Assets balances
        self.balance = {}
        mark_prices = {p["symbol"]: p["price"] for p in self.client.ticker_price()}
        for b in self.account["balances"]:
            free = float(b["free"])
            locked = float(b["locked"])
            price = float(mark_prices.get(b["asset"] + self.quote_asset, 0.0))
            if free or locked:
                self.balance[b["asset"]] = {
                    "free": free,
                    "locked": locked,
                    "markPrice": price,
                }
        # Current open orders
        self.positions = {}
        positions = self.client.get_open_orders()
        for p in positions:
            # Calculate unrealized profit
            pos_amount = float(p["origQty"])
            entry_price = float(p["price"])
            mark_price = mark_prices.get(p["symbol"])
            direction = Direction.BULLISH if p["type"] == "BUY" else Direction.BEARISH
            un_profit = (mark_price - entry_price) * direction
            # Only store data if has an open position
            if pos_amount:
                self.positions[p["symbol"]] = {
                    "unrealizedProfit": un_profit,
                    "positionAmount": pos_amount,
                    "side": p["side"],
                    "type": p["type"],
                    "entryPrice": entry_price,
                }
        print("\r{:<80}".format(""), end="\r")

    def sell_all_assets(self):
        for asset, p in self.balance.items():
            symbol = asset + self.quote_asset
            if p["free"]:
                response = self.create_order(
                    symbol=symbol,
                    direction=Direction.BEARISH,
                    qty=p["free"],
                    price=p["markPrice"],
                )
                if "ERROR" in response:
                    print(response)
                else:
                    # Update message
                    print(
                        " {} {} {} {} @ {} {}".format(
                            I.CHECK,
                            C.Style("Sell", C.RED),
                            p["free"],
                            asset,
                            round(p["markPrice"] * p["free"], 4),
                            self.quote_asset,
                        )
                    )

    def get_candlestick_data(self, _symbol, _timeframe, _qty):
        """Query Binance for candlestick data"""
        raw_data = self.client.klines(symbol=_symbol, interval=_timeframe, limit=_qty)
        # Set up the return array
        converted_data = []
        # Convert each element into a Python dictionary object, then add to converted_data
        for candle in raw_data:
            # Dictionary object
            converted_candle = {
                "time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": candle[6],
                "quote_asset_volume": float(candle[7]),
                "number_of_trades": int(candle[8]),
                "taker_buy_base_asset_volume": float(candle[9]),
                "taker_buy_quote_asset_volume": float(candle[10]),
            }
            converted_data.append(converted_candle)
        # Return converted data
        return converted_data

    def get_data_from_exchange(self, symbol, timeframe):
        """Convert binance data into a dataframe"""
        # Retrieve the raw data from Binance
        raw_data = self.get_candlestick_data(symbol, timeframe, self.candle_count)
        # Transform raw_data into a Pandas DataFrame
        df_data = DataFrame(raw_data)
        # Convert the time to human readable format
        df_data["time"] = readable_time(df_data["time"])
        df_data["close_time"] = readable_time(df_data["close_time"])
        # Update self.candlesticks
        self.candlesticks.update({f"{symbol}-{timeframe}": df_data})

    def create_order(
        self,
        symbol: str,
        direction: int,
        qty: float,
        price: float,
        sl: "float | None" = None,
        tp: "float | None" = None,
    ) -> str:
        """Creates an order on Binance and its SL and TP orders

        Parameters
        ----------
        `symbol`: pair to trade (e.g. "BTCBUSD")

        `direction`: Direction of the trade

        `qty`: amount of the trade

        `price`: mark price of the asset

        `sl`: stop loss price

        `tl`: take profit price or callback rate if trailing"""
        # Close all previous open positions for that symbol
        self.client.cancel_open_orders(symbol=symbol)
        # Filters
        step_size = str_to_decimal_places(self.symbols[symbol]["step_size"])
        tick_size = str_to_decimal_places(self.symbols[symbol]["tick_size"])
        qty = round_float_to_str(
            number=min(max(qty, self.symbols[symbol]["min_qty"]), self.symbols[symbol]["max_qty"]),
            decimal_places=step_size,
        )
        # Main order arguments
        ## Type MARKET so SL and TP can be ordered rightaway
        order_kwargs = {
            "symbol": symbol,
            "side": side_from_direction(direction=direction),
            "type": "MARKET",
            "quantity": qty,
        }
        order_response = C.Style("Order: ", C.DARKCYAN) + self.place_order(
            response_args=["origQty"], kwargs=order_kwargs
        ).replace("origQty", "Qty")
        # Change direction for SL and TP
        direction *= -1
        # Stop loss arguments
        if not I.CROSS in order_response and sl is not None:
            # Args
            sl_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction),
                "type": "STOP_LOSS_LIMIT",
                "timeInForce": "GTC",
                "quantity": qty,
                "stopPrice": round_float_to_str(number=(price + sl) / 2, decimal_places=tick_size),  # Trigger
                "price": round_float_to_str(number=sl, decimal_places=tick_size),  # SL
            }
            sl_response = C.Style("Stop Loss: ", C.DARKCYAN) + (
                self.place_order(response_args=["price", "stopPrice"], kwargs=sl_kwargs)
                .replace("price", "Activate")
                .replace("stopPrice", "Limit")
            )
        # Take profit arguments
        if not I.CROSS in order_response and tp is not None:
            # Args
            tp_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction),
                "type": "TAKE_PROFIT_LIMIT",
                "timeInForce": "GTC",
                "quantity": qty,
                "stopPrice": round_float_to_str(number=(price + tp) / 2, decimal_places=tick_size),  # Trigger
                "price": round_float_to_str(number=tp, decimal_places=tick_size),  # TP
            }
            tp_response = C.Style("Take Profit: ", C.DARKCYAN) + (
                self.place_order(response_args=["price", "stopPrice"], kwargs=tp_kwargs)
                .replace("price", "Activate")
                .replace("stopPrice", "Limit")
            )
        # Return responses
        response = f"{order_response} - Mark price {price}"
        if sl_response:
            response += C.Style(" | ", C.DARKCYAN) + sl_response
        if tp_response:
            response += C.Style(" | ", C.DARKCYAN) + tp_response
        return response

    def place_order(self, response_args: list[str], kwargs) -> str:
        try:
            # Place the order
            order_response = self.client.new_order(**kwargs)
            if not order_response.get("orderId"):
                # Order not placed
                raise Exception(kwargs)
            # Success... Return responses
            return " - ".join([f"{a} {order_response[a]}" for a in response_args])
        # ----------------------------------
        # An error ocurred...
        except ClientError as error:
            error_data = {"code": error.error_code, "msg": error.error_message}
        except Exception as error:
            error_data = error
        # Return error message
        return "{icon} {message} -> {args}".format(
            icon=I.CROSS,
            message=C.Style("[{}] {}".format(error_data["code"], error_data["msg"]), C.RED),
            args=kwargs,
        )
