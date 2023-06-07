from binance.error import ClientError
from binance.um_futures import UMFutures
from pandas import DataFrame

from scripts.common import readable_time, round_float_to_str, side_from_direction, str_to_decimal_places
from scripts.console import C, I
from scripts.exchange import ExchangeInterface


class BinanceFutures(ExchangeInterface):
    candlesticks: dict[str, DataFrame] = {}
    positions: dict[str, dict[str, str]] = {}

    def __init__(
        self, test_mode: bool, api_key: str, secret_key: str, quote_asset: str, candle_count: int = 1000
    ) -> None:
        try:
            params = {"key": api_key, "secret": secret_key}
            if test_mode:
                params["base_url"] = "https://testnet.binancefuture.com"
            self.client = UMFutures(**params)
            print(I.CHECK, "Successful connection to account")
            self.account = {}
            self.balance = None
            self.candle_count = candle_count
            self.quote_asset = quote_asset
            self.test_mode = test_mode
            self.query_quote_asset_list()
            self.update_account_data()
        except Exception as ex:
            print(C.Style(I.CROSS + " Error @ binance_conn.get_account ::", C.BOLD, C.RED), ex)

    def query_quote_asset_list(self):
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
                if filter["filterType"] == "LOT_SIZE":
                    data.update(
                        {
                            "min_qty": float(filter["minQty"]),
                            "max_qty": float(filter["maxQty"]),
                            "step_size": filter["stepSize"],
                        }
                    )
                if filter["filterType"] == "PRICE_FILTER":
                    data.update(
                        {
                            "tick_size": filter["tickSize"],
                        }
                    )
            symbols[row["symbol"]] = data
        self.symbols = symbols

    def update_account_data(self) -> None:
        """Retrieves updated data from Binance Futures account"""
        # Update console
        print("\r", end=" " * 100)
        print(C.Style(f"\r{I.CLOCK} Updating account data ... ", C.DARKCYAN), end="")
        # Update account
        data = self.client.account()
        # Account Balances
        for asset in data["assets"]:
            # Store self.quote_asset data
            if asset["asset"] == self.quote_asset:
                self.account = {
                    "canTrade": data["canTrade"],
                    "crossWalletBalance": float(asset["crossWalletBalance"]),
                    "crossUnPnl": float(asset["crossUnPnl"]),
                    "availableBalance": float(asset["availableBalance"]),
                    "updateTime": asset["updateTime"],
                }
        # Positions
        self.positions = {}
        mark_prices = {p["symbol"]: p["price"] for p in self.client.ticker_price()}
        for p in data["positions"]:
            # Only store data if has an open position
            if float(p["positionAmt"]):
                self.positions[p["symbol"]] = {
                    "unrealizedProfit": float(p["unrealizedProfit"]),
                    "positionAmount": float(p["positionAmt"]),
                    "entryPrice": float(p["entryPrice"]),
                    "markPrice": float(mark_prices.get(p["symbol"], 0.0)),
                }
        print("\r{:<80}".format(""), end="\r")

    def get_server_time(self) -> int:
        """Retrieves current server's timestamp"""
        return self.client.time()["serverTime"]

    def get_candlestick_data(self, _symbol, _timeframe, _qty):
        """Query Binance for candlestick data"""
        # Set up the return array
        converted_data = []
        # Retrieve data from Exchange
        raw_data = self.client.mark_price_klines(symbol=_symbol, interval=_timeframe, limit=_qty)
        # Convert each element into a Python dictionary object, then add to converted_data
        for candle in raw_data:
            # Dictionary object
            converted_candle = {
                "time": int(candle[0]),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": int(candle[6]),
                "quote_asset_volume": float(candle[7]),
                "number_of_trades": int(candle[8]),
                "taker_buy_base_asset_volume": float(candle[9]),
                "taker_buy_quote_asset_volume": float(candle[10]),
            }
            converted_data.append(converted_candle)
        # Return converted data
        return converted_data

    def get_data_from_exchange(self, symbol: str, timeframe: str) -> None:
        """Retrieve candlesticks values in a Dataframe for each asset in the specified timeframe"""
        # Get the last self.candle_count candlesticks
        raw_data = self.get_candlestick_data(symbol, timeframe, self.candle_count)
        # Transform raw_data into a Pandas DataFrame
        df_data = DataFrame(raw_data)
        # Convert the time to human readable format
        df_data["time"] = readable_time(df_data["time"])
        # df_data["close_time"] = readable_time(df_data["close_time"])
        # Update self.candlesticks
        self.candlesticks.update({f"{symbol}-{timeframe}": df_data})

    def create_order(
        self,
        symbol: str,
        direction: int,
        qty: float,
        price: float,
        trailing: bool = True,
        sl: "float | None" = None,
        tp: "float | None" = None,
        leverage: int = 1,
    ) -> str:
        """Creates an order on Binance and its SL and TP orders

        Parameters
        ----------
        `symbol`: pair to trade (e.g. "BTCBUSD")

        `direction`: Direction of the trade

        `qty`: amount of the trade

        `price`: mark price of the asset

        `trailing`: whether to trail stop or not

        `sl`: stop loss price

        `tl`: take profit price or callback rate if trailing

        `leverage`: by default doesn't use leverage"""
        # Close all previous open positions for that symbol
        self.client.cancel_open_orders(symbol=symbol)
        # Set leverage
        try:
            self.client.change_leverage(symbol=symbol, leverage=leverage)
        except ClientError as error:
            # Return error message
            return "{icon} {message}".format(
                icon=I.CROSS,
                message=C.Style("[{}] {}".format(error.error_code, error.error_message), C.RED),
            )
        # Filters
        step_size = str_to_decimal_places(self.symbols[symbol]["step_size"])
        tick_size = str_to_decimal_places(self.symbols[symbol]["tick_size"])
        qty = min(max(qty, self.symbols[symbol]["min_qty"]), self.symbols[symbol]["max_qty"])
        qty = round_float_to_str(number=qty, decimal_places=step_size)
        # Main order arguments
        ## Type MARKET so SL and TP can be ordered rightaway
        order_kwargs = {
            "symbol": symbol,
            "side": side_from_direction(direction=direction),
            "positionSide": "BOTH",
            "type": "MARKET",
            "quantity": qty,
            "reduceOnly": "false",
        }
        order_response = C.Style("Order: ", C.DARKCYAN) + self.place_order(
            response_args=["origQty"], kwargs=order_kwargs
        ).replace("origQty", "Qty")
        sl_response = tp_response = None
        # Change direction for SL and TP
        direction *= -1
        # Stop loss arguments
        if not I.CROSS in order_response and sl is not None:
            # Args
            sl_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction),
                "positionSide": "BOTH",
                "type": "STOP_MARKET",
                "stopPrice": round_float_to_str(number=sl, decimal_places=tick_size),  # SL
                "closePosition": "true",
                "workingType": "MARK_PRICE",
            }
            sl_response = C.Style("Stop Loss: ", C.DARKCYAN) + (
                self.place_order(response_args=["stopPrice"], kwargs=sl_kwargs)
                .replace("stopPrice", "Price")
            )
        # Take profit arguments
        if not I.CROSS in order_response and tp is not None:
            # Activation price: 0.1% away from price
            act_price = price * (1 + 0.001 * direction)
            act_price = round_float_to_str(number=act_price, decimal_places=tick_size)
            if trailing:
                cr = min(max(tp, 1), 5)
                # Activation price: 2/3 way from price to target
                targ_price = price * (1 - cr * direction / 100)
                act_price = (price + 2 * targ_price) / 3
                act_price = round_float_to_str(number=act_price, decimal_places=tick_size)
                tp_kwargs = {
                    "symbol": symbol,
                    "side": side_from_direction(direction=direction),
                    "positionSide": "BOTH",
                    "type": "TRAILING_STOP_MARKET",
                    "activationPrice": act_price,
                    "quantity": qty,
                    "reduceOnly": "true",
                    "callbackRate": round_float_to_str(number=cr, decimal_places=1),
                    "workingType": "MARK_PRICE",
                }
                tp_response = C.Style("Trailing Take Profit: ", C.DARKCYAN) + (
                    self.place_order(response_args=["activatePrice", "priceRate"], kwargs=tp_kwargs)
                    .replace("activatePrice", "Activate")
                    .replace("priceRate", "Trailing%")
                )
            else:
                tp_kwargs = {
                    "symbol": symbol,
                    "side": side_from_direction(direction=direction),
                    "positionSide": "BOTH",
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": round_float_to_str(number=tp, decimal_places=tick_size),  # TP
                    "closePosition": "true",
                    "workingType": "MARK_PRICE",
                }
                tp_response = C.Style("Take Profit: ", C.DARKCYAN) + (
                    self.place_order(response_args=["stopPrice"], kwargs=tp_kwargs)
                    .replace("stopPrice", "Price")
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
