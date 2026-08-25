"""
Historical data management.
Handles data loading, caching, and validation.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from logger_config import get_logger
from data.cache import CacheManager

logger = get_logger(__name__)

class HistoricalDataManager:
    """Manage historical data loading and caching."""
    
    def __init__(self, data_provider, cache_manager: CacheManager, data_dir: Path):
        self.data_provider = data_provider
        self.cache = cache_manager
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True, parents=True)
    
    def get_historical_data(self, symbol: str, days: int = 365, timeframe: str = '1d') -> pd.DataFrame:
        """Get historical data with caching."""
        
        # Check cache first
        cache_key = self.cache.get('historical', symbol, timeframe, days)
        if cache_key is not None:
            logger.info(f"Using cached historical data for {symbol}")
            return cache_key
        
        # Fetch from provider
        logger.info(f"Fetching historical data for {symbol} ({days} days)")
        ohlcv_data = self.data_provider.get_ohlcv(symbol, timeframe, limit=days*2)  # Extra buffer
        
        if not ohlcv_data:
            logger.error(f"Failed to get historical data for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.vwap
            }
            for bar in ohlcv_data
        ])
        
        df.set_index('timestamp', inplace=True)
        
        # Filter to requested period
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        df = df[df.index >= cutoff_date]
        
        # Cache the data
        self.cache.set('historical', df, symbol, timeframe, days, ttl_seconds=3600)
        
        logger.info(f"Got {len(df)} historical bars for {symbol}")
        return df
    
    def get_intraday_data(self, symbol: str, timeframe: str = '5m') -> pd.DataFrame:
        """Get intraday data for current trading day."""
        
        # Check cache
        cache_key = self.cache.get('intraday', symbol, timeframe)
        if cache_key is not None:
            logger.info(f"Using cached intraday data for {symbol}")
            return cache_key
        
        # Fetch from provider
        logger.info(f"Fetching intraday data for {symbol}")
        ohlcv_data = self.data_provider.get_intraday_data(symbol, timeframe)
        
        if not ohlcv_data:
            logger.error(f"Failed to get intraday data for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.vwap
            }
            for bar in ohlcv_data
        ])
        
        df.set_index('timestamp', inplace=True)
        
        # Cache for 1 minute
        self.cache.set('intraday', df, symbol, timeframe, ttl_seconds=60)
        
        logger.info(f"Got {len(df)} intraday bars for {symbol}")
        return df
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, float]:
        """Validate data quality."""
        
        if df.empty:
            return {'quality_score': 0.0, 'freshness_score': 0.0}
        
        quality_score = 100.0
        
        # Check for missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
        quality_score -= missing_pct * 50
        
        # Check for price gaps
        df['gap_pct'] = abs(df['close'].pct_change())
        extreme_gaps = (df['gap_pct'] > 0.10).sum()  # Gaps > 10%
        quality_score -= extreme_gaps * 2
        
        # Check for zero volume
        zero_volume = (df['volume'] == 0).sum()
        quality_score -= zero_volume * 1
        
        # Freshness score
        last_timestamp = df.index[-1]
        age_hours = (datetime.utcnow() - last_timestamp).total_seconds() / 3600
        
        if age_hours < 1:
            freshness_score = 100.0
        elif age_hours < 4:
            freshness_score = 75.0
        elif age_hours < 24:
            freshness_score = 50.0
        else:
            freshness_score = 0.0
        
        quality_score = max(0, min(100, quality_score))
        
        return {
            'quality_score': quality_score,
            'freshness_score': freshness_score,
            'missing_pct': missing_pct,
            'age_hours': age_hours
        }
