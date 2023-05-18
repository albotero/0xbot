from abc import ABCMeta, abstractmethod
from pandas import DataFrame

from scripts.indicators.indicator import Direction


class ExchangeInterface(metaclass=ABCMeta):
    account: "dict[str, bool | float | int]"
    candlesticks: dict[str, DataFrame]
    balance: "dict[str, dict[str, float]] | None"
    positions: dict[str, dict[str, float]]
    symbols: "dict[str, dict[str, str | float]]"
    quote_asset: str
    test_mode: bool

    @abstractmethod
    def get_server_time(self) -> int:
        pass

    @abstractmethod
    def get_candlestick_data(self, _symbol, _timeframe, _qty) -> None:
        pass

    @abstractmethod
    def get_data_from_exchange(self, symbol: str, timeframe: str) -> None:
        pass

    @abstractmethod
    def create_order(
        self,
        symbol: str,
        direction: Direction,
        qty: float,
        price: float,
        trailing_sl: bool,
        sl: float = None,
        tp: float = None,
        leverage: int = 1,
    ) -> str:
        pass

    @abstractmethod
    def update_account_data(self) -> None:
        pass
