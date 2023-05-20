import json
import os
import sys
from typing import Any

from scripts.exchanges.binance_futures import BinanceFutures
from scripts.exchanges.binance_spot import BinanceSpot
from scripts.console import C, I
from scripts.examples import divergences_example, technical_analysis_example

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
    }


def select_strategy() -> "tuple[str | Any]":
    """Select one of the defined strategies to run"""
    # Implement strategies
    strategies = [
        ("Technical Analysis Example", technical_analysis_example.strategy),
        ("Divergences Example", divergences_example.strategy),
    ]
    # No strategies in the list
    if len(strategies) == 0:
        raise NotImplementedError
    # Multiple strategies, select one
    strategy_index = 0
    if len(strategies) > 1:
        loop = True
        while loop:
            try:
                print()
                print("You have multiple strategies defined:")
                for n, strategy in enumerate(strategies):
                    print(C.Style(f"  [{n+1}] {strategy[0]}", C.DARKCYAN))
                strategy_index = int(input("Which strategy would you like to use? Only text its number: "))
                if strategy_index < 1 or strategy_index > len(strategies):
                    raise ValueError
                loop = False
                print()
            except ValueError:
                # If value is not int or it is > than max for the strategies list
                print(
                    C.Style(I.CROSS + " Error @ main ::", C.BOLD, C.RED),
                    C.Style("Invalid strategy number", C.RED),
                )
    # Return selected or default tuple
    return strategies[strategy_index - 1]


def main():
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
                # Run the strategy
                strategy = select_strategy()
                print(
                    I.CHECK,
                    "Running {} @ {} {}".format(
                        C.Style(strategy[0], C.DARKCYAN),
                        C.Style("Binance", C.DARKCYAN),
                        C.Style(settings["market"], C.DARKCYAN),
                    ),
                )
                try:
                    strategy[1](exchange=bn, market=settings["market"])
                except KeyboardInterrupt:
                    print()
                    main()


if __name__ == "__main__":
    try:
        # Clear screen
        os.system("cls||clear")
        # Run script
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()
