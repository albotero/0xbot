import json
import os

from scripts.exchanges.binance_futures import BinanceFutures
from scripts.exchanges.binance_spot import BinanceSpot
from scripts.console import C, I
from scripts.strategies.technical_analysis import technical_analysis

settings_path = "bot-config.json"


def get_settings():
    """Read settings from settings"""
    if os.path.exists(settings_path):
        f = open(settings_path, "r")
        settings = json.load(f)
        f.close()
        return settings


def load_bot_config():
    """Load data from bot-config"""
    # Import settings
    bot_config = get_settings()
    # Check Test Mode
    test_mode = bot_config.get("test-mode", True)
    print(C.Style("\n ~ TEST MODE ~" if test_mode else "\n ~ LIVE MODE ~", C.BOLD, C.PURPLE), end="\n\n")
    # Load data
    exchange = bot_config.get("exchanges", {}).get("binance", {})
    keys = exchange.get("test" if test_mode else "live", {})
    market = exchange.get("market", "futures")
    api_key = keys.get(f"api-{market}" if test_mode else "api")
    secret_key = keys.get(f"secret-{market}" if test_mode else "secret")
    quote_asset = exchange.get("quote-asset", "BUSD")
    if api_key is None or secret_key is None:
        print(C.Style(I.CROSS + " Error @ load_bot_config ::", C.BOLD, C.RED), C.Style("API keys not provided", C.RED))
        return
    return {
        "market": market,
        "exchange": [test_mode, api_key, secret_key, quote_asset],
        "strategies": bot_config.get("strategies"),
    }


def main():
    # Clear screen
    os.system("cls||clear")
    # Load bot-config
    settings = load_bot_config()
    if settings:
        # Retrieve account information
        if settings["market"] == "futures":
            bn = BinanceFutures(*settings["exchange"])
        elif settings["market"] == "spot":
            bn = BinanceSpot(*settings["exchange"])
        else:
            print(
                C.Style(I.CROSS + " Error @ load_bot_config ::", C.BOLD, C.RED),
                C.Style("No valid market provided", C.RED),
            )
            return
        if bn.account:
            if bn.account["canTrade"]:
                technical_analysis(exchange=bn, market=settings["market"])


if __name__ == "__main__":
    main()
