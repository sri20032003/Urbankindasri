"""
Abstract base class for all data providers.
Supports pluggable implementations (YFinance, Zerodha, NSE API, etc.)
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class OHLCV:
    """OHLCV bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float = None
    
class BaseDataProvider(ABC):
    """Abstract base for all data providers."""
    
    @abstractmethod
    def get_live_price(self, symbol: str) -> Tuple[float, datetime, float]:
        """Get current price, timestamp, and volume.
        Returns: (price, timestamp, volume)
        """
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> List[OHLCV]:
        """Get historical OHLCV data.
        timeframe: '1m', '5m', '15m', '1h', '1d', '1w'
        Returns: List of OHLCV bars in ascending order
        """
        pass
    
    @abstractmethod
    def get_intraday_data(self, symbol: str, timeframe: str = "5m") -> List[OHLCV]:
        """Get intraday data for current trading day.
        """
        pass
    
    @abstractmethod
    def get_vwap(self, symbol: str, date: datetime = None) -> float:
        """Get Volume Weighted Average Price.
        """
        pass
    
    @abstractmethod
    def get_live_bid_ask(self, symbol: str) -> Tuple[float, float, float]:
        """Get live bid, ask, and spread.
        Returns: (bid, ask, spread_bps)
        """
        pass
    
    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> Dict:
        """Get corporate actions (splits, dividends, bonus, etc.).
        """
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Dict:
        """Get stock metadata (sector, market cap, etc.).
        """
        pass
    
    @abstractmethod
    def search_symbols(self, query: str) -> List[str]:
        """Search for symbols matching query.
        """
        pass
    
    def health_check(self) -> bool:
        """Check if data provider is operational.
        """
        try:
            self.get_live_price("RELIANCE")
            return True
        except:
            return False
