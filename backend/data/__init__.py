# Base Data Provider Interface

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OHLCVData(BaseModel):
    """OHLCV data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None
    
    class Config:
        from_attributes = True


class StockData(BaseModel):
    """Stock price and metadata."""
    symbol: str
    exchange: str  # NSE, BSE
    current_price: float
    previous_close: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_qty: Optional[int] = None
    ask_qty: Optional[int] = None
    timestamp: datetime
    ohlcv_data: List[OHLCVData]
    source: str
    quality_score: float  # 0-1
    freshness_score: float  # 0-1
    
    class Config:
        from_attributes = True


class BaseDataProvider(ABC):
    """Abstract base class for market data providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.source_name = self.__class__.__name__
        logger.info(f"Initializing {self.source_name}")
    
    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[OHLCVData]:
        """Fetch OHLCV data.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
            limit: Number of bars to fetch
            start_date: Start date for historical data
            end_date: End date for historical data
        
        Returns:
            List of OHLCV data points
        """
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> StockData:
        """Fetch current price and market data.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Current stock data
        """
        pass
    
    @abstractmethod
    async def get_quote(self, symbols: List[str]) -> Dict[str, StockData]:
        """Fetch quotes for multiple symbols.
        
        Args:
            symbols: List of stock symbols
        
        Returns:
            Dictionary of symbol -> StockData
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if data provider is accessible.
        
        Returns:
            True if provider is healthy
        """
        pass
    
    def _calculate_quality_score(
        self,
        data_points: int,
        missing_values: int,
        age_minutes: float
    ) -> float:
        """Calculate data quality score (0-1).
        
        Based on:
        - Number of data points received
        - Missing or null values
        - Data freshness
        """
        if data_points == 0:
            return 0.0
        
        completeness = 1.0 - (missing_values / data_points)
        
        # Freshness: degrade score based on age
        if age_minutes < 1:
            freshness = 1.0
        elif age_minutes < 5:
            freshness = 0.95
        elif age_minutes < 15:
            freshness = 0.85
        elif age_minutes < 60:
            freshness = 0.70
        else:
            freshness = max(0.5, 1.0 - (age_minutes / 1440))  # < 0.5 for > 1 day
        
        quality = (completeness * 0.7) + (freshness * 0.3)
        return max(0.0, min(1.0, quality))
