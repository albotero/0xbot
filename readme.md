# 0xBot Trading Software

`0xbot` is a python project created to perform automatic trading in crypto exchanges 24/7.
Initially it can trade any pair in Binance exchange through their API.

# First of all ...

- This project is based in James Hinton's [How to Build a Crypto Trading Bot with Binance and Python](https://medium.com/coinmonks/how-to-build-a-crypto-trading-bot-with-binance-and-python-connect-to-binance-9e69bb320c24) tutorial, I would like to thank him for his awesome article series.

* This bot intends to be a valuable tool to help people make a profit from crypto trading, however, the strategies I code here are of my own design and aren't an investment advice.

* **_Always_ do your own research _(DYOR)_** before make any investment with this bot or any other financial tool. This applies both for trading strategies and for trading pairs!

* **_Never_ invest money you aren't willing to lose**: please don't use with the money of your house's mortgage!

* Use it under your own risk and always test it thoroughly using testnet API keys before using the bot with your real account API keys spending real money in it.

* This is an open software, you may use and distribute it. Feel free to check the code, clone it and make your own changes... But remember to thank!

# Setup

## Requirements

Make sure you have python3 installed by running:

```console
$ python3 --version
```

In case you don't have it installed, the previous command will get an error, please follow this [guide](https://realpython.com/installing-python/) to install it in your OS.

## Clone repository & Install requirements

Use the following commands to clone this repository:

```console
$ git clone https://github.com/albotero/0xbot
$ cd 0xbot
$ pip3 install -r requirements.txt
```

## Settings file

Create a file named `bot-config.json` in the root folder. Be sure it is added to the `.gitignore` file since its contents are sensitive.
This file is used both to get credentials to connect to the exchanges as well as to customize the strategies.

Set the contents of the file with the following code:

```json
{
  "test-mode": false,
  "exchanges": {
    "binance": {
      "quote-asset": "BUSD",
      "test": {
        "api": "paste_here_your_binance_testnet_api_key",
        "secret": "paste_here_your_binance_testnet_secret_key"
      },
      "live": {
        "api": "paste_here_your_binance_api_key",
        "secret": "paste_here_your_binance_secret_key"
      }
    }
  },
  "strategies": {
    "pump": {
      "candle-count": 3,
      "percentage-rise": 0.5,
      "quote-per-trade": 20,
      "timeframe": "30m"
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

This software uses `binance-connector-python` script to make API calls. Visit its [GitHub Repo](https://github.com/binance/binance-connector-python) for detailed info.

### <li>Testnet</li>

When you created `bot-config.json` file you specified test mode by default. This mode allows to test the script and its strategies and functionality, as well as search for bugs, before use your real API keys _(i.e. actual money)_.

You will need a pair of API/Secret keys for the Binance's Spot Testnet, visit [Binance FAQs](https://www.binance.com/en/support/faq/how-to-test-my-functions-on-binance-testnet-ab78f9a1b8824cf0a106b4229c76496d) to learn how to get them.

### <li>Real-world API keys</li>

Once you are confident with the bot functioning and your trading strategy, update `bot-config.json` to disable test mode and check you have already added your account's API keys, which you can generate from [Binance API Dashboard](https://www.binance.com/en/my/settings/api-management):

```json
{
  "test-mode": false,
  ...
}
```

</ol>

# Usage

## Run

To start the bot, just run the main script:

```console
$ python3 main.py
```

## Trading Pairs

After a successful connection to Binance API is made, all trading pairs against the specified quote _(e.g. BUSD)_ are retrieved along with the trading commisions charged by the exchange. The strategy will be run over all these pairs. Currently only _Spot Trading_ is implemented.

Default quote BUSD can be modified in `bot-config.json`

When running in test mode only 6 trading pairs with BUSD quote are provided by the exchange. There are ~317 assets in live mode.

## Previous balances

If the account has free balances of any of the retrieved assets that can be traded against the quote, user will be prompted whether to sell them or not before running the bot:

![Screenshot of previous balances sold](/res/img/previous-balances.png "Screenshot of previous balances sold")

Please note that actual sold amount may be less than account balance for this asset, since market fees are charged by and step size is limited by the exchange. The rest of the asset is going to remain in your account as dust.

## Analysis

The analysis refers to the strategy development. Each asset is analyzed and, if defined conditions are met, a buy or sell order is emitted.

At the end of each analysis this data will appear:

- **Long orders:** Current open positions _(i.e. bought assets)_. Asset symbol _(e.g. BTC)_, entry price _(i.e. price at which the asset was bought)_, mark price _(i.e. current price of the asset against the quote)_ and unrealized profit of that order are provided.

- **Unrealized profit:** Global profit since the start of the strategy, includes appreciation/devaluation of assets that haven't been sold yet.

- **Realized profit:** Global profit since the start of the strategy, only include assets that were bought and then sold back.

Once the strategy is deployed and after each analysis, an `... idle ...` message will appear until the current candle in the selected timeframe closes and the next analysis can be done.

!["Screenshot of Pump Strategy analysis"](/res/img/pump-analysis.png "Screenshot of Pump Strategy analysis")

# Trading Strategies

Currently the _Pump Strategy_ is the only one implemented so it is used by default. In a latter version when more strategies are added, user will be prompted at start to select which one to use.

## Pump

Pump strategy checks last _n_ candles, and if all of them closed over a determined percentage from the previous one, the asset is bought to seize the uptrend.

Once any latter candle price closes at or less than 50% of its predecesor's body, the asset is sold to either realize the profit or cut losses.

### Settings

You may configure the strategy through `bot-config.json`:

- **"candle-count":** Number of candles to be analyzed in order to define whether a pump in price is going on. **_Default: 3_**
- **"percentage-rise":** How much a candle needs to rise respect the previous one to be counted as part of a pump. Use percentage without the symbol _(e.g. for 1% just input 1)_. **_Default: 0.5_**
- **"quote-per-trade":** Value of each order to be made based in the quote asset _(e.g. BUSD)_. **_Default: 20_**
- **"timeframe":** Timeframe for candlesticks to be analyzed. **_Default: "30m"_**

![Screenshot of Pump Strategy running](/res/img/pump-live.png "Screenshot of Pump Strategy running")

## Technical Analysis

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

## Machine Learning (ML)

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

# Risk Management

## Investment limits

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

## Stop loss (SL)

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

## Trailing SL

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

## Take profit (TP)

&#x1F6A7; &#x1F477; &#x1F6E0;&#xFE0F; Under construction! &#x1F6E0;&#xFE0F; &#x1F477; &#x1F6A7;

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
