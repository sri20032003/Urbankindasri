"""DataManager - Unified data ingestion and caching"""
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataManager:
    """Manages OHLCV data from NSE/BSE through multiple providers."""

    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = config.get('cache_ttl_seconds', 300)
        self.last_update = {}

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = '1d',
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a symbol."""
        try:
            # Check cache
            cache_key = f"{symbol}_{interval}"
            if cache_key in self.cache:
                age = (datetime.now() - self.last_update[cache_key]).total_seconds()
                if age < self.cache_ttl:
                    logger.debug(f"Cache hit for {cache_key}")
                    return self.cache[cache_key]

            # Fetch fresh data
            logger.info(f"Fetching {symbol} {interval} data")
            
            # Convert NSE symbol to Yahoo format
            ticker_symbol = self._convert_symbol(symbol)
            
            # Use yfinance as default provider
            data = yf.download(
                ticker_symbol,
                period='1y' if interval == '1d' else '100d',
                interval=interval,
                progress=False
            )

            if data.empty:
                logger.warning(f"No data received for {symbol}")
                return None

            # Standardize columns
            data.columns = ['open', 'high', 'low', 'close', 'volume']
            data = data.tail(limit)
            
            # Cache
            self.cache[cache_key] = data
            self.last_update[cache_key] = datetime.now()
            
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    async def store_signal(self, signal: Dict):
        """Store generated signal (placeholder for DB integration)."""
        logger.info(f"Storing signal for {signal.get('symbol')}")
        # TODO: Integrate with database
        pass

    def _convert_symbol(self, nse_symbol: str) -> str:
        """Convert NSE symbol to Yahoo Finance format."""
        # Example: RELIANCE -> RELIANCE.NS, TCS -> TCS.NS
        return f"{nse_symbol}.NS" if not nse_symbol.endswith('.NS') else nse_symbol
