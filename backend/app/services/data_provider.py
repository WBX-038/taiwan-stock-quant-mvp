from abc import ABC, abstractmethod

import pandas as pd

from app.models import DataPoint


class MarketDataProvider(ABC):
    @abstractmethod
    def get_price_history(self, symbol: str, period: str = "2y") -> DataPoint:
        raise NotImplementedError

    @abstractmethod
    def get_info(self, symbol: str) -> DataPoint:
        raise NotImplementedError

    @abstractmethod
    def get_fast_info(self, symbol: str) -> DataPoint:
        raise NotImplementedError


def empty_history() -> pd.DataFrame:
    return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"])
