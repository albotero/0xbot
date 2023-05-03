from scripts.exchanges.binance_conn import BinanceConn
from scripts.console import C, I
from scripts.strategy import Strategy
from scripts.strategies.pump import Pump
import json
import os

settings_path = "bot-config.json"


def get_settings():
    ''' Read settings from settings '''
    if os.path.exists(settings_path):
        f = open(settings_path, "r")
        settings = json.load(f)
        f.close()
        return settings


def load_bot_config():
    ''' Load data from bot-config'''
    # Import settings
    bot_config = get_settings()
    # Check Test Mode
    test_mode = bot_config.get("test-mode", True)
    print(C.Style("\n ~ TEST MODE ~" if test_mode else "\n ~ LIVE MODE ~", C.BOLD, C.PURPLE), end="\n\n")
    # Set the keys
    exchange = bot_config.get("exchanges", {}).get("binance", {})
    keys = exchange.get("test" if test_mode else "live", {})
    api_key = keys.get("api")
    secret_key = keys.get("secret")
    quote_asset = exchange.get("quote-asset", "BUSD")
    if api_key is None or secret_key is None:
        print(C.Style(I.CROSS + " Error @ load_bot_config ::", C.BOLD, C.RED), C.Style("API keys not provided", C.RED))
        return
    return {"exchange": [test_mode, api_key, secret_key, quote_asset], "strategies": bot_config.get("strategies")}


def main():
    # Clear screen
    os.system('cls||clear')
    # Load bot-config
    settings = load_bot_config()
    if settings:
        # Retrieve account information
        binance_conn = BinanceConn(*settings["exchange"])
        if binance_conn.account:
            # Retrieve market data
            if binance_conn.account['canTrade']:
                # Check if has assets other than Quote Asset
                assets_count, balances = binance_conn.check_account_balances()
                if assets_count:
                    # Asks if user wants to sell them
                    print(f"\nYou have assets on your account other than quote ({binance_conn.quote_asset}):")
                    for symbol, balance in balances.items():
                        free, max_qty = balance
                        print(f"  {I.COIN}  {C.Style(symbol, C.DARKCYAN)} Balance: {free}",
                              f"- Max order: {max_qty}" if free > max_qty else "")
                    if input(f"Do you want to sell them for {binance_conn.quote_asset}? (y/n): ").lower() == "y":
                        binance_conn.sell_all_assets(balances)
                # Run strategy
                strategy_settings = settings["strategies"]["pump"]
                pump_strategy = Strategy(
                    exchange=binance_conn,
                    strategy=Pump(
                        candle_count=strategy_settings["candle-count"],
                        percentage_rise=strategy_settings["percentage-rise"]),
                    quote_per_trade=strategy_settings["quote-per-trade"],
                    timeframe=strategy_settings["timeframe"])
                while True:
                    pump_strategy.analyze_symbols()


if __name__ == "__main__":
    main()
