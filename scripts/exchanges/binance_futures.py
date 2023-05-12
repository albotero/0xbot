from binance.error import ClientError
from binance.um_futures import UMFutures
from pandas import DataFrame

from scripts.common import readable_time, side_from_direction
from scripts.console import C, I
from scripts.exchanges.exchange import ExchangeInterface
from scripts.indicators.indicator import Direction


class BinanceFutures(ExchangeInterface):
    candlesticks: dict[str, DataFrame] = {}
    positions: dict[str, dict[str, str]] = {}

    def __init__(
        self, test_mode: bool, api_key: str, secret_key: str, quote_asset: str, candle_count: int = 200
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
        print(C.Style(f"{I.CLOCK} Receiving assets data ...", C.DARKCYAN), end="")
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
                "precision": row["baseAssetPrecision"],
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
        df_data["close_time"] = readable_time(df_data["close_time"])
        # Update self.candlesticks
        self.candlesticks.update({f"{symbol}-{timeframe}": df_data})

    def create_order(
        self,
        symbol: str,
        direction: Direction,
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

        `price`: price for the limit order

        `trailing`: whether to trail stop or not

        `sl`: stop loss price

        `tl`: take profit price or callback rate if trailing

        `leverage`: by default doesn't use leverage

        Returns
        -------
        Order IDs if successful or error message"""
        # Set leverage
        self.client.change_leverage(symbol=symbol, leverage=leverage)
        # Main order arguments
        order_kwargs = {
            "symbol": symbol,
            "side": side_from_direction(direction=direction),
            "positionSide": "BOTH",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": str(qty),
            "price": str(price),
            "reduceOnly": "false",
        }
        # Change direction for SL and TP
        direction *= -1
        # Stop loss arguments
        if sl is not None:
            # Trailing SL: 0.1% ≤ Callback rate ≤ 5%
            sl = min(max(sl, 0.1), 5) if trailing else sl
            # Activation price for limits: middle between price and limit
            sl_limit = (price + sl) / 2
            # Args
            sl_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction),
                "positionSide": "BOTH",
                "type": "STOP",
                "price": str(sl_limit),
                "stopPrice": str(sl),
                "closePosition": "true",
                "workingType": "MARK_PRICE",
            }
        # Take profit arguments
        if tp is not None:
            # Activation price for limits: middle between price and limit
            tp_limit = (price + tp) / 2
            # Args
            if trailing:
                sl_kwargs = {
                    "symbol": symbol,
                    "side": side_from_direction(direction=direction),
                    "positionSide": "BOTH",
                    "type": "TRAILING_STOP_MARKET",
                    "activationPrice": str(tp_limit),
                    "quantity": str(qty),
                    "reduceOnly": "true",
                    "callbackRate": str(tp),
                    "workingType": "MARK_PRICE",
                }
            else:
                tp_kwargs = {
                    "symbol": symbol,
                    "side": side_from_direction(direction=direction),
                    "positionSide": "BOTH",
                    "type": "TAKE_PROFIT",
                    "price": str(tp_limit),
                    "stopPrice": str(tp),
                    "closePosition": "true",
                    "workingType": "MARK_PRICE",
                }
        # Place the trades
        executed_trades: list[int] = []
        try:
            # Close all previous open positions for that symbol
            self.client.cancel_open_orders(symbol=symbol)
            # Place the order
            order_response = self.client.new_order(**order_kwargs)
            if not order_response.get("orderId"):
                # Order not placed
                raise Exception(order_response)
            executed_trades.append(int(order_response["orderId"]))
            # Place the SL
            sl_response = self.client.new_order(**sl_kwargs)
            if not sl_response.get("orderId"):
                # Order not placed
                raise Exception(sl_response)
            executed_trades.append(sl_response["orderId"])
            # Place the TP
            tp_response = self.client.new_order(**tp_kwargs)
            if not tp_response.get("orderId"):
                # Order not placed
                raise Exception(tp_response)
            executed_trades.append(tp_response["orderId"])
            # Success... Return responses
            return "Order ID: {order} {separator} SL ID: {sl} {separator} TP ID: {tp}".format(
                separator=C.Style(" | ", C.DARKCYAN),
                order=order_response["orderId"],
                sl=sl_response["orderId"],
                tp=tp_response["orderId"],
            )
        # ----------------------------------
        # An error ocurred...
        except ClientError as error:
            error_data = {"code": error.error_code, "msg": error.error_message}
        except Exception as error:
            error_data = error
        # Close all active positions for that symbol
        try:
            for t in executed_trades:
                self.client.cancel_order(symbol=symbol, orderId=t)
        except ClientError as error:
            error_data = {"code": error.error_code, "msg": error.error_message}
        # Return error message
        return "{icon} {error} {message}".format(
            icon=I.CROSS,
            error=C.Style("ERROR", C.RED, C.BOLD),
            message=C.Style("[{}] {}".format(error_data["code"], error_data["msg"]), C.RED),
        )
