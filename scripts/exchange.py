from abc import ABCMeta, abstractmethod
from pandas import DataFrame

from scripts.objects.coin import Coin


class ExchangeInterface(metaclass=ABCMeta):
    quote_asset: str
    stop_loss: float
    symbols: dict[str, Coin]
    test_mode: bool

    @abstractmethod
    def get_data_from_exchange(self, symbol: str, timeframe: str, qty: int) -> DataFrame: pass

    @abstractmethod
    def trade_at_market(self, side: str, asset: Coin, amount: float) -> dict[str, float]: pass
