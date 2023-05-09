from binance.error import ClientError
from binance.spot import Spot
from pandas import DataFrame
from scripts.common import readable_time, side_from_direction
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
                "precision": row["quoteAssetPrecision"],
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
        print(C.Style(f"{I.CLOCK} Updating account data ...", C.DARKCYAN), end="")
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
        # Update console
        print(f"\r{I.CHECK} Account data updated{'':<20}")

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
        direction: Direction,
        qty: float,
        price: float,
        sl: float = None,
        tp: float = None,
    ) -> str:
        """Creates an order on Binance and its SL and TP orders

        Parameters
        ----------
        symbol: pair to trade (e.g. "BTCBUSD")
        direction: Direction of the trade
        qty: amount of the trade
        price: price for the limit order
        sl: stop loss price
        tl: take profit price

        Returns
        -------
        Order IDs if successful or error message"""
        # Floats to Strings
        qty = str(qty)
        price = str(price)
        # Main order arguments
        order_kwargs = {
            "symbol": symbol,
            "side": side_from_direction(direction=direction),
            "positionSide": "BOTH",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": qty,
            "price": price,
            "reduceOnly": "false",
        }
        # Stop loss arguments
        if sl is not None:
            sl_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction * -1),
                "positionSide": "BOTH",
                "type": "STOP_MARKET",
                "quantity": qty,
                "stopPrice": sl,
                "workingType": "MARK_PRICE",
            }
        # Take profit arguments
        if tp is not None:
            tp_kwargs = {
                "symbol": symbol,
                "side": side_from_direction(direction=direction * -1),
                "positionSide": "BOTH",
                "type": "TAKE_PROFIT_MARKET",
                "quantity": qty,
                "stopPrice": str(tp),
                "workingType": "MARK_PRICE",
            }
        # Place the trades
        executed_trades = []
        try:
            # Close all previous open positions for that symbol
            self.client.cancel_open_orders(symbol=symbol)
            # Place the order
            order_response = self.client.new_order(**order_kwargs)
            if not order_response.get("orderId"):
                # Order not placed
                raise Exception(order_response)
            executed_trades.append(order_response["orderId"])
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
        for t in executed_trades:
            self.client.cancel_order(symbol=symbol, orderId=t)
        # Return error message
        return "{icon} {error} {message}".format(
            icon=I.CROSS,
            error=C.Style("ERROR", C.RED, C.BOLD),
            message=C.Style("[{}] {}".format(error_data["code"], error_data["msg"]), C.RED),
        )
