import json
import numpy
from binance.error import ClientError
from binance.spot import Spot
from pandas import DataFrame, to_datetime
from scripts.common import float_to_precision, round_float
from scripts.exchange import ExchangeInterface
from scripts.objects.coin import Coin
from scripts.console import C, I


class BinanceConn(ExchangeInterface):

    def __init__(self, test_mode, api_key, secret_key, quote_asset):
        # Get client from binance
        if test_mode:
            client = Spot(base_url="https://testnet.binance.vision", key=api_key, secret=secret_key)
        else:
            client = Spot(key=api_key, secret=secret_key)
        # Get account
        try:
            print(I.CHECK, "Successful connection to account")
            self.client = client
            self.account = client.account()
            self.quote_asset = quote_asset
            self.symbols = self.query_quote_asset_list(quote_asset_symbol=quote_asset)
            self.test_mode = test_mode
            self.maker_fee = float(self.account["commissionRates"]["maker"])
            self.taker_fee = float(self.account["commissionRates"]["taker"])
            print(I.WARNING, C.Style("Comissions:", C.YELLOW),
                  f"maker {self.maker_fee * 100:.3f}% | taker {self.taker_fee * 100:.3f}%")
        except Exception as ex:
            print(C.Style(I.CROSS + " Error @ binance_conn.get_account ::", C.BOLD, C.RED), ex)

    def query_quote_asset_list(self, quote_asset_symbol):
        ''' Retrieve quotes of crypto against Quote '''
        # Update console
        print(C.Style(f"{I.CLOCK} Receiving assets data ...", C.DARKCYAN), end="")
        # Retrieve data
        symbol_dictionary = self.client.exchange_info()
        # Convert into a dataframe
        symbol_dataframe = DataFrame(symbol_dictionary['symbols'])
        # Extract only those symbols with a base asset of Quote and status of TRADING
        quote_symbol_dataframe = symbol_dataframe.loc[symbol_dataframe['quoteAsset'] == quote_asset_symbol]
        quote_symbol_dataframe = quote_symbol_dataframe.loc[quote_symbol_dataframe['status'] == "TRADING"]
        # Update console
        print(f"\r{I.CHECK} Received assets list", " "*10)
        # Return list
        symbols = {}
        for _, row in quote_symbol_dataframe.iterrows():
            data = {
                "symbol": row["symbol"],
                "base": row["baseAsset"],
                "quote": row["quoteAsset"],
                "precision": row["quoteAssetPrecision"]}
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
            symbols[row["symbol"]] = Coin(**data)
        return symbols

    def check_account_balances(self):
        assets_count = 0
        balances = {}
        for balance in self.account['balances']:
            asset = self.symbols.get(balance["asset"] + self.quote_asset)
            free = float(balance["free"])
            if asset and free and balance["asset"] != self.quote_asset and free >= asset.min_qty:
                assets_count += 1
                balances[balance["asset"]] = (free, asset.max_qty)
        return assets_count, balances

    def sell_all_assets(self, balances):
        for asset, balance in balances.items():
            asset = self.symbols.get(asset + self.quote_asset)
            if asset:
                try:
                    response = self.trade_at_market(side="SELL", asset=asset, amount=balance[0])
                    if response.get("error"):
                        raise Exception(response["error"])
                    amount = float(response["amount"])
                    price = float(response["price"])
                    # Update message
                    print(" ", I.CHECK, C.Style(asset.strsymbol, C.DARKCYAN), C.Style("Sell", C.RED),
                          f"{amount} {asset.base} @ {round(price * amount, 4)} {asset.quote}")
                except Exception as error:
                    print(" ", I.CROSS, C.Style(asset.strsymbol, C.DARKCYAN), C.Style("SELL ERROR", C.RED), error)

    def get_candlestick_data(self, _symbol, _timeframe, _qty):
        ''' Query Binance for candlestick data '''
        raw_data = self.client.klines(symbol=_symbol, interval=_timeframe, limit=_qty)
        # Set up the return array
        converted_data = []
        # Convert each element into a Python dictionary object, then add to converted_data
        for candle in raw_data:
            # Dictionary object
            converted_candle = {
                'time': candle[0],
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5]),
                'close_time': candle[6],
                'quote_asset_volume': float(candle[7]),
                'number_of_trades': int(candle[8]),
                'taker_buy_base_asset_volume': float(candle[9]),
                'taker_buy_quote_asset_volume': float(candle[10])
            }
            converted_data.append(converted_candle)
        # Return converted data
        return converted_data

    def get_data_from_exchange(self, symbol, timeframe, qty):
        ''' Convert binance data into a dataframe '''
        # Retrieve the raw data from Binance
        raw_data = self.get_candlestick_data(symbol, timeframe, qty)
        # Transform raw_data into a Pandas DataFrame
        df_data = DataFrame(raw_data)
        # Convert the time to human readable format
        df_data["time"] = self.readable_time(df_data["time"])
        df_data["close_time"] = self.readable_time(df_data["close_time"])
        # Calculate trend
        df_data["trend"] = numpy.where((df_data["open"] < df_data["close"]), 'bull', 'bear')
        # Return the dataframe
        return df_data

    def readable_time(self, time):
        return to_datetime(time, unit="ms", utc=True).map(lambda x: x.tz_convert("America/Bogota"))

    def make_trade(self, params):
        ''' Execute a trade on the exchange and returns

        https://binance-docs.github.io/apidocs/spot/en/#new-order-trade '''
        try:
            # Make the trade
            response = self.client.new_order(**params)
            fills_price = 0.0
            fills_qty = 0
            for fill in response["fills"]:
                fills_price += float(fill["price"]) * float(fill["qty"])
                fills_qty += float(fill["qty"])
            avg_price = fills_price / fills_qty
            return {
                "amount": float(response["origQty"]),
                "price": avg_price
            }
        except ClientError as error:
            message = json.loads(error.message)
            return {"error": "[{code}] {message}".format(code=message["code"], message=message["msg"])}

    def trade_at_market(self, side: str, asset: Coin, amount: float):
        ''' Trade amount of the asset at market price

        side: "BUY" | "SELL"'''
        # Market order -> Taker fee
        qty = min(amount, asset.max_qty) * (1 - self.taker_fee)
        lot_qty = round_float(qty, asset.step_size)
        str_qty = float_to_precision(lot_qty, asset.precision)
        return self.make_trade(params={
            "symbol": asset.symbol,
            "side": side,
            "type": "MARKET",
            "quantity": str_qty
        })
