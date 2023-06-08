# 0xBot Trading Software

`0xbot` is a python project created to perform automatic trading in crypto exchanges 24/7.
Initially it can trade any pair in Binance exchange through their API.

# First of all ...

- This project was inspired by James Hinton's [How to Build a Crypto Trading Bot with Binance and Python](https://medium.com/coinmonks/how-to-build-a-crypto-trading-bot-with-binance-and-python-connect-to-binance-9e69bb320c24) tutorial, I would like to thank him for his awesome article series.

* This bot intends to be a valuable tool to help people make a profit from crypto trading, however, the strategies I code here are of my own design and aren't an investment advice.

* **_Always_ do your own research _(DYOR)_** before make any investment with this bot or any other financial tool. This applies both for trading strategies and for trading pairs!

* **_Never_ invest money you aren't willing to lose**: please don't use with the money of your house's mortgage!

* Use it under your own risk and always test it thoroughly using testnet API keys before using the bot with your real account API keys and spending real money in it.

* This is an open software, you may use and distribute it as you wish. Feel free to check the code, clone it and make your own changes... But remember to thank!

* Pull requests are welcome. For major changes, please open an issue first
  to discuss what you would like to change.

# Setup

## Requirements

Make sure you have python3 installed by running:

```console
$ python3 --version
```

In case you don't have it installed, the previous command will throw an error, please follow this [guide](https://realpython.com/installing-python/) to install it in your OS.

## Clone repository & Install requirements

Use the following commands to clone this repository:

```console
$ git clone https://github.com/albotero/0xbot
$ cd 0xbot
$ pip3 -m venv .venv
$ source .venv/bin/activate
(venv)$ pip3 install -r requirements.txt
```

## Settings file

Create a file named `bot-config.json` in the root folder. Be sure it is added to the `.gitignore` file since its contents are sensitive.
This file is used to store the credentials to connect to the exchanges. Set the contents of the file with the following code:

```json
{
  "test-mode": true,
  "exchanges": {
    "binance": {
      "quote-asset": "USDT",
      "market": "futures",
      "test": {
        "api-futures": "paste_here_your_binance_futures_testnet_api_key",
        "secret-futures": "paste_here_your_binance_futures_testnet_secret_key",
        "api-spot": "paste_here_your_binance_spot_testnet_api_key",
        "secret-spot": "paste_here_your_binance_spot_testnet_secret_key"
      },
      "live": {
        "api": "paste_here_your_binance_api_key",
        "secret": "paste_here_your_binance_secret_key"
      }
    }
  }
}
```

# Exchanges

## Binance

<ol type="a">

### <li>Registration</li>

If you are going to use it and don't have a Binance account yet and you register using [my referral link](https://accounts.binance.com/register?ref=99626596) I would deeply appreciate it!

### <li>API script</li>

This software uses `binance-connector-python` script to make API calls. Visit its [GitHub Repo](https://github.com/binance/binance-connector-python) for details.

### <li>Testnet</li>

When you created `bot-config.json` file test mode was set by default. This mode allows you to test the script and its strategies and functionality, as well as search for bugs, before use your real API keys _(i.e. actual money)_.

You will need a pair of API/Secret keys for the Binance's Spot and Futures testnets, visit [How to Test My Functions on Binance Testnet](https://www.binance.com/en/support/faq/how-to-test-my-functions-on-binance-testnet-ab78f9a1b8824cf0a106b4229c76496d) to learn how to generate them.

### <li>Real-world API keys</li>

Once you are confident with the bot functioning and your trading strategy, update `bot-config.json` to disable test mode. Check you have already added your account's API keys, which you can generate from [Binance API Dashboard](https://www.binance.com/en/my/settings/api-management):

```json
{
  "test-mode": false,
  ...
}
```

Check you have allowed both futures and spot trading in API dashboard, as well as your IP address is whitelisted for the bot to successfully run.

</ol>

## Connection to the account

The exchange's API is accessed and managed through the `ExchangeInterface` class. Implementation of this interface for both Binance Spot and Futures are located within the `scripts/exchanges` folder.

You may write your own `ExchangeInterface` implementation if you want to use the bot with another Exchange.

# Setting up the Strategy

In order to emit long (buy) or short (sell) positions, the logic starts with an `Indicator` that uses candlesticks data obtained from the exchange for its own calculations. The `Signal` object checks the data generated from these Indicators and emits the long or short signals according to the previously defined parameters. The `SpotStrategy` and `FuturesStrategy` classes use these signals to place the corresponding orders in the exchange's account.

Take a look at the examples of some strategies in `scripts/examples` folder for further details.

## Indicators

These indicators are implemented:

<!-- prettier-ignore -->
| Indicator | Type | Parameters | Data headers† |
| :---: | :---: | :---: | :---: |
| ADX (Average Directional Index) | Trend | `data`: DataFrame <br/> `periods`: int (optional, default = 14) | -di(`periods`) <br/> adx(`periods`) <br/> +di(`periods`) <br/> adx-diff(`periods`) |
| ATR (Average True Range) | Volatility | `data`: DataFrame <br/> `periods`: int (optional, default = 14) <br/> `return_data`: *Ignore this* | atr(`periods`) |
| Bollinger Bands | Volatility | `data`: DataFrame <br/> `periods`: int (optional, default = 20) <br/> `std_count`: int (optional, default = 2) | bb-l(`periods`) <br/> bb-m(`periods`) <br/> bb-u(`periods`) |
| DEMA (Double Exponential Moving Average) | Trend | `data`: DataFrame <br/> `periods`: int | dema(`periods`) |
| Divergence | Trend | `indicator`: Indicator <br/> `indicator_header`: str <br/> `periods`: int (optional, default = 50) | None‡ |
| EMA (Exponential Moving Average) | Trend | `data`: DataFrame <br/> `periods`: int | ema(`periods`) |
| MACD (Moving Averages Convergence Divergence) | Momentum | `data`: DataFrame <br/> `short_term`: int (optional, default = 12) <br/> `long_term`: int (optional, default = 26) <br/> `signal`: int (optional, default = 9) | macd(`short_term`, `long_term`) <br/> macd-s(`short_term`, `long_term`, `signal`) <br/> macd-h(`short_term`, `long_term`, `signal`) <br/> macd-ma(`short_term`, `long_term`, `signal`) |
| RSI (Relative Strength Index) | Momentum | `data`: DataFrame <br/> `periods`: int (optional, default = 14) | rsi(`periods`) |
| SMA (Simple Moving Average) | Trend | `data`: DataFrame <br/> `periods`: int | sma(`periods`) |
| Stochastic oscillator | Momentum | `data`: DataFrame <br/> `periods`: int (optional, default = 14) <br/> `slow_periods`: int (optional, default = 3) | stoch-k(`periods`) <br/> stoch-d(`periods`) <br/> stoch-diff(`periods`) |

†Analyzed data with each indicator will be added to the pandas DataFrame in these columns. They are used in Signal implementation.
‡Divergence class returns directly a BULLISH, BEARISH or NEUTRAL signal.

## Signals

The `Signal` object checks indicator's data output to define a BEARISH / BULLISH / NEUTRAL signal::

<!-- prettier-ignore -->
| Type | Parameters | Description |
| :---: | :---: | :---: |
| Cross signal | `signal_ind` <br/> `signal_header` <br/> `base_ind` <br/> `base_header` | Returns BULLISH if previous signal was ≤ base and current signal is > base <br/> Returns BEARISH if previous signal was ≥ base and current signal is < base |
| Indicator above/below Indicator | `signal_ind` <br/> `signal_header` <br/> `buy_limit` <br/> `sell_limit` <br/> `reverse` _(Optional)_ | Returns BULLISH if signal is below base. If `reverse = True` returns BEARISH <br/> Returns BEARISH if signal is above base. If `reverse = True` returns BULLISH |
| Price above/below Indicator | `signal_ind` = None <br/> `signal_header` = "close" <br/> `buy_limit` <br/> `sell_limit` <br/> `reverse` _(Optional)_ | Returns BULLISH if price is below base. If `reverse = True` returns BEARISH <br/> Returns BEARISH if price is above base. If `reverse = True` returns BULLISH |

### Modifiers

The following options can be set to customize the indicator signals:

- `base_limit: boolean`: whether to use base indicator as a limit for BULLISH or BEARISH signal.

- `consolidation_header` and `consolidation_limit`: only analyze `signal_header` if `consolidation_header` value is above `consolidation_limit`.

- `signal_ind = None`: to get signal not from an indicator but to use raw `signal_header` data (e.g. close, open, etc).

- `reverse: boolean`: to reverse signal direction (i.e. BEARISH to BULLISH and BULLISH to BEARISH, respectively).

- `rising: boolean`: to determine whether the indicator is rising or not. May be used with reverse to determine if it is plummeting.

## Trading Strategies

You may create your own strategies by using any of the available indicators. A strategy consist of an object of type `FuturesStrategy` or `SpotStrategy`.

### Futures Strategy

The `FuturesStrategy` declaration takes these parameters:

<!-- prettier-ignore -->
| Parameter | Definition |
| :---: | :---: |
| `name` | Custom name to identify the strategy on command line |
| `exchange` | Exchange interface that was used to connect to the account |
| `signals` | List of Signal objects with the desired Indicators |
| `order_value` | Percentage of the account's balance to be used in each trade. _Value: int 0 to 100_.
| `risk_reward_ind` | Percentage for stop loss _(int 0 to 100)_ or Indicator object _(e.g. ATR)_. |
| `risk_reward_ratio` | Expected reward ratio. _Value: int (e.g. 3 for a reward ratio 1:3)_. |
| `timeframe` | Candlesticks timeframe: <br /> _1m_ \| _3m_ \| _5m_ \| _15m_ \| _30m_ \| _1h_ \| _2h_ \| _4h_ \| _6h_ \| _8h_ \| _12h_ \| _1d_ \| _3d_ \| _1w_ \| _1M_ |
| `leverage` | Leverage for the trades. _Value: int (e.g. 5 for 5x)_.
| `min_signals_percentage` | Percentage of signals with the same output _(i.e. BEARISH or BULLISH)_ to define to place an order. _Value: float 0 to 1_. |
| `trailing_stop` | Whether to use trailing take profit if true or to use limit take profit if false. _Value: bool_. |
| `chart_type` | Type of candlesticks to use. _Value: "candle" (default) or "heikin_ashi"_. |

For example, a `FuturesStrategy` can be defined as follows:

```python
strategy = FuturesStrategy(
  name="Divergence",
  exchange=exchange,
  leverage=5, # 5x leverage
  order_value=0.5, # 0.5% of wallet balance as margin for each trade
  signals=signals, # Array of signals
  timeframe="1h",
  risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
  risk_reward_ratio=2.5, # Risk:Reward 1:2.5
  trailing_stop=True,
)
```

### Spot Strategy

The `SpotStrategy` declaration takes these parameters:

<!-- prettier-ignore -->
| Parameter | Definition |
| :---: | :---: |
| `name` | Custom name to identify the strategy on command line |
| `exchange` | Exchange interface that was used to connect to the account |
| `signals` | List of Signal objects with the desired Indicators |
| `order_value` | Percentage of the account's balance to be used in each trade. _Value: int 0 to 100_.
| `risk_reward_ind` | Percentage for stop loss _(int 0 to 100)_ or Indicator object _(e.g. ATR)_. |
| `risk_reward_ratio` | Expected reward ratio. _Value: int (e.g. 3 for a reward ratio 1:3)_. |
| `timeframe` | Candlesticks timeframe: <br /> _1m_ \| _3m_ \| _5m_ \| _15m_ \| _30m_ \| _1h_ \| _2h_ \| _4h_ \| _6h_ \| _8h_ \| _12h_ \| _1d_ \| _3d_ \| _1w_ \| _1M_ |
| `min_signals_percentage` | Percentage of signals with the same output _(i.e. BEARISH or BULLISH)_ to define to place an order. _Value: float 0 to 1_. |
| `chart_type` | Type of candlesticks to use. _Value: "candle" (default) or "heikin_ashi"_. |

For example, a `SpotStrategy` can be defined as follows:

```python
strategy = SpotStrategy(
    name="Divergence",
    exchange=exchange,
    order_value=2.5, # 2.5% of wallet balance in each trade
    signals=signals, # Array of signals
    timeframe="30m",
    risk_reward_ind=Indicator(Indicator.TYPE_ATR, {"periods": 14}),
    risk_reward_ratio=2.5, # Risk:Reward 1:2.5
)
```

## Stop loss (SL) and Take profit (TP)

SL and TP are set for each trade according to Risk/Reward settings. Both a specific percentage of asset's price or an indicator value (e.g. ATR) may be used to calculate them:

For example, if settings define `risk_reward_ind = 0.5` and `risk_reward_ratio = 2`, SL will be placed 0.5% away from current mark price and TP will be set 1% away. If settings define an indicator such as ATR (e.g. `risk_reward_ind = Indicator(Indicator.TYPE_ATR)` and `risk_reward_ratio = 2`), SL will be placed `1 * ATR` away from current mark price and TP will be set `2 * ATR` away.

If `trailing_tp = True` then trailing TP percentage will be calculated according to settings explained in the former paragraph.

## Execute the Strategy

To run a strategy, just loop a call to strategy's `check_signals` function:

```python
while True:
    strategy.check_signals()
```

Refer to `scripts/examples` folder for some examples of how to implement a strategy.

# Usage

## Run

To start the bot, just run the main script:

```console
(venv)$ python3 main.py
```

## Trading Pairs

After a successful connection to Binance account, all trading pairs against the specified quote _(e.g. USDT)_ are retrieved along with the trading commisions charged by the exchange if the selected market is Spot. The strategy will be run over all these pairs.

Default quote USDT can be modified in `bot-config.json`. Check Fee Tiers for each quote asset at [Binance Fee Rate](https://www.binance.com/en/fee).

## Strategy selection

After trading data is retrieved from the Binance account, the bot will look for your strategy, and if many are defined, you will be prompted for which one to use:

![Screenshot of strategy selection prompt](/res/img/strategy-selection.png "Screenshot of strategy selection prompt")

## Current positions

If you have open positions and balances in your account, they will be printed at start and after each analysis:

![Screenshot of futures positions](/res/img/balances-futures.png "Screenshot of futures positions")

![Screenshot of spot balances](/res/img/balances-spot.png "Screenshot of spot balances")

## Strategy running

Once the bot is set up, after each candle close, all the symbols will be analyzed for the conditions defined in the running strategy. After each analysis, the current positions or balances are printed and a counter will appear until next candle close.

![Screenshot of strategy running](/res/img/running-futures.png "Screenshot of strategy running")

# Last but not least ...

If this project has been useful to you and you want to support me, feel free to do it by these ways:

- Donate via Crypto:
  <!-- prettier-ignore -->
  | Network | Wallet address |
  |:---:|:---:|
  | <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png" alt="Bitcoin" title="Bitcoin" width="20" height="20" style="margin-bottom: -5px;"> | bc1q7n8ne2740hwxzldl88vwug95m5rrjxw5a480rh |
  | <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1027.png" alt="Ethereum" title="Ethereum" width="20" height="20" style="margin-bottom: -5px;"> <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1839.png" alt="BSC" title="Binance Smart Chain (BSC)" width="20" height="20" style="margin-bottom: -5px;"><br/><img src="https://s2.coinmarketcap.com/static/img/coins/64x64/3890.png" alt="Polygon" title="Polygon" width="20" height="20" style="margin-bottom: -5px;"> <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/5994.png" alt="Shiba Inu" title="Shiba Inu"   width="27" height="27" style="margin: 0 -4px -9px -3.5px;"> ... | 0xB72030640bAD1f25CD596E14554Cb8833970011E |
  | <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/74.png" alt="Dogecoin" title="Dogecoin" width="20" height="20" style="margin-bottom: -5px;"> | DF6Sn9dMmWV3fxT4sGuMHw2Bz3X28HoiDv |
  | <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/2.png" alt="Litecoin" title="Litecoin" width="20" height="20" style="margin-bottom: -5px;"> | ltc1q2ca9tvl9ru9zz6khdcuq6wdp08fsfu7sakm3p4 |

- Visit my [LinkedIn profile](https://www.linkedin.com/in/botdev92/) and write a Recommendation!

- Follow me on [Twitter](https://twitter.com/botdev92).
