"""
YFinance data provider implementation.
Uses free yfinance library for Indian stock data.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from logger_config import get_logger
from data.base_provider import BaseDataProvider, OHLCV

logger = get_logger(__name__)

class YFinanceProvider(BaseDataProvider):
    """YFinance data provider for NSE/BSE stocks."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_live_price(self, symbol: str) -> Tuple[float, datetime, float]:
        """Get current price from YFinance."""
        try:
            # Add .NS for NSE or .BO for BSE
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period='1d')
            
            if data.empty:
                logger.warning(f"No data for {symbol}")
                return None, None, None
            
            close = data['Close'].iloc[-1]
            volume = data['Volume'].iloc[-1]
            timestamp = data.index[-1]
            
            logger.info(f"Got live price for {symbol}: {close}")
            return float(close), timestamp, float(volume)
        
        except Exception as e:
            logger.error(f"Error fetching live price for {symbol}: {str(e)}")
            return None, None, None
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 100) -> List[OHLCV]:
        """Get historical OHLCV data."""
        try:
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            
            # Map timeframe to yfinance period
            period_map = {
                '1m': '60d',
                '5m': '60d',
                '15m': '60d',
                '1h': '1y',
                '1d': '5y',
                '1w': '5y'
            }
            
            period = period_map.get(timeframe, '1y')
            data = ticker.history(period=period, interval=timeframe)
            
            if data.empty:
                logger.warning(f"No OHLCV data for {symbol}")
                return []
            
            # Convert to OHLCV objects
            bars = []
            for idx, row in data.tail(limit).iterrows():
                bar = OHLCV(
                    timestamp=idx,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume']),
                    vwap=self._calculate_vwap([row])  # Simplified
                )
                bars.append(bar)
            
            logger.info(f"Got {len(bars)} OHLCV bars for {symbol}")
            return bars
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {str(e)}")
            return []
    
    def get_intraday_data(self, symbol: str, timeframe: str = "5m") -> List[OHLCV]:
        """Get intraday data for current trading day."""
        return self.get_ohlcv(symbol, timeframe, limit=100)
    
    def get_vwap(self, symbol: str, date: datetime = None) -> float:
        """Calculate VWAP."""
        try:
            if date is None:
                date = datetime.now()
            
            # Get intraday data
            data = self.get_intraday_data(symbol, '5m')
            
            if not data:
                return None
            
            # Calculate VWAP: sum(price * volume) / sum(volume)
            numerator = sum(bar.close * bar.volume for bar in data)
            denominator = sum(bar.volume for bar in data)
            
            vwap = numerator / denominator if denominator > 0 else None
            logger.info(f"VWAP for {symbol}: {vwap}")
            return vwap
        
        except Exception as e:
            logger.error(f"Error calculating VWAP for {symbol}: {str(e)}")
            return None
    
    def get_live_bid_ask(self, symbol: str) -> Tuple[float, float, float]:
        """Get bid-ask spread.
        Note: YFinance doesn't provide real-time bid-ask.
        Returning close price ± 0.05%
        """
        try:
            price, _, _ = self.get_live_price(symbol)
            
            if price is None:
                return None, None, None
            
            # Estimate spread (0.05% typical for liquid stocks)
            spread_pct = 0.0005
            bid = price * (1 - spread_pct / 2)
            ask = price * (1 + spread_pct / 2)
            spread_bps = (ask - bid) / price * 10000
            
            logger.info(f"Bid-Ask for {symbol}: {bid:.2f}-{ask:.2f} ({spread_bps:.2f} bps)")
            return float(bid), float(ask), float(spread_bps)
        
        except Exception as e:
            logger.error(f"Error fetching bid-ask for {symbol}: {str(e)}")
            return None, None, None
    
    def get_corporate_actions(self, symbol: str) -> Dict:
        """Get corporate actions."""
        try:
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            
            return {
                "splits": ticker.splits.to_dict() if hasattr(ticker, 'splits') and not ticker.splits.empty else {},
                "dividends": ticker.dividends.to_dict() if hasattr(ticker, 'dividends') and not ticker.dividends.empty else {},
            }
        
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {str(e)}")
            return {}
    
    def get_stock_info(self, symbol: str) -> Dict:
        """Get stock metadata."""
        try:
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get('longName', symbol),
                "sector": info.get('sector', 'Unknown'),
                "industry": info.get('industry', 'Unknown'),
                "market_cap": info.get('marketCap', 0),
                "beta": info.get('beta', 1.0),
                "pe_ratio": info.get('trailingPE', 0),
                "dividend_yield": info.get('dividendYield', 0),
            }
        
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return {}
    
    def search_symbols(self, query: str) -> List[str]:
        """Search for symbols.
        Note: YFinance doesn't have a search API.
        This is a placeholder.
        """
        logger.warning("YFinance doesn't support symbol search. Use NIFTY_50_SYMBOLS instead.")
        return []
    
    def _calculate_vwap(self, data: List[Dict]) -> float:
        """Helper to calculate VWAP."""
        if not data:
            return None
        
        numerator = sum(row['Close'] * row['Volume'] for row in data)
        denominator = sum(row['Volume'] for row in data)
        
        return numerator / denominator if denominator > 0 else None
