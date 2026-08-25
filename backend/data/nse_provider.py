# Yahoo Finance Data Provider

import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from .base_provider import BaseDataProvider, OHLCVData, StockData
import pandas as pd

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance data provider for NSE/BSE stocks."""
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[OHLCVData]:
        """Fetch OHLCV data from Yahoo Finance."""
        try:
            # Convert symbol format (RELIANCE.NS for NSE, RELIANCE.BO for BSE)
            ticker = yf.Ticker(symbol)
            
            # Default to end_date = today, start_date based on limit
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                # Estimate start_date based on timeframe and limit
                if timeframe == "1m":
                    days = limit / 1440  # ~1440 minutes per day
                elif timeframe == "5m":
                    days = limit / 288   # ~288 5-min candles per day
                elif timeframe == "15m":
                    days = limit / 96    # ~96 15-min candles per day
                elif timeframe == "1h":
                    days = limit / 6.5   # ~6.5 hourly candles per trading day
                elif timeframe == "1d":
                    days = limit * 1.2
                elif timeframe == "1wk":
                    days = limit * 7 * 1.2
                elif timeframe == "1mo":
                    days = limit * 30 * 1.2
                else:
                    days = limit
                start_date = end_date - timedelta(days=days)
            
            # Fetch historical data
            df = ticker.history(start=start_date, end=end_date, interval=timeframe)
            
            if df.empty:
                logger.warning(f"No data received for {symbol}")
                return []
            
            # Convert to OHLCVData
            ohlcv_list = []
            for idx, row in df.iterrows():
                ohlcv = OHLCVData(
                    timestamp=idx.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adj_close=float(row.get('Adj Close', row['Close']))
                )
                ohlcv_list.append(ohlcv)
            
            # Sort by timestamp
            ohlcv_list.sort(key=lambda x: x.timestamp)
            
            # Limit to requested number
            return ohlcv_list[-limit:]
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {str(e)}")
            return []
    
    async def get_current_price(self, symbol: str) -> StockData:
        """Fetch current price and market data."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0.0))
            bid = info.get('bid', None)
            ask = info.get('ask', None)
            bid_size = info.get('bidSize', None)
            ask_size = info.get('askSize', None)
            
            # Fetch recent OHLCV data
            ohlcv_data = await self.get_ohlcv(symbol, "1d", 30)
            
            # Extract exchange from symbol
            exchange = "NSE" if symbol.endswith(".NS") else "BSE" if symbol.endswith(".BO") else "NSE"
            
            stock_data = StockData(
                symbol=symbol,
                exchange=exchange,
                current_price=float(current_price) if current_price else 0.0,
                previous_close=float(previous_close) if previous_close else 0.0,
                bid=float(bid) if bid else None,
                ask=float(ask) if ask else None,
                bid_qty=int(bid_size) if bid_size else None,
                ask_qty=int(ask_size) if ask_size else None,
                timestamp=datetime.now(),
                ohlcv_data=ohlcv_data,
                source=self.source_name,
                quality_score=self._calculate_quality_score(
                    len(ohlcv_data),
                    0,
                    0.0
                ),
                freshness_score=1.0
            )
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            return None
    
    async def get_quote(self, symbols: List[str]) -> Dict[str, StockData]:
        """Fetch quotes for multiple symbols."""
        quotes = {}
        for symbol in symbols:
            try:
                stock_data = await self.get_current_price(symbol)
                if stock_data:
                    quotes[symbol] = stock_data
            except Exception as e:
                logger.error(f"Error fetching quote for {symbol}: {str(e)}")
        
        return quotes
    
    async def health_check(self) -> bool:
        """Check if Yahoo Finance is accessible."""
        try:
            ticker = yf.Ticker("RELIANCE.NS")
            data = ticker.info
            return bool(data.get('currentPrice') or data.get('regularMarketPrice'))
        except Exception as e:
            logger.error(f"Yahoo Finance health check failed: {str(e)}")
            return False
