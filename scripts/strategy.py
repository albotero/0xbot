from abc import ABCMeta, abstractmethod
from scripts.exchange import ExchangeInterface

class StrategyInterface(metaclass=ABCMeta):
    """ Defines a new strategy
     
    Parameters
    ----------
    exchange: Interface of the exchange
    market: "futures" or "spot"
    name: Name to identify on command line
    strategy: Function itself"""

    exchange: ExchangeInterface
    market: str
    name: str

    def __init__(self, exchange: ExchangeInterface, market: str, name: str) -> None:
        self.exchange = exchange
        self.market = market
        self.name = name
    
    @abstractmethod
    def strategy(self): pass