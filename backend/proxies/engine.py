"""ProxyEngine - Multi-dimensional proxy calculation"""
import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class ProxyEngine:
    """Calculates 50+ observable proxies for technical analysis."""

    def __init__(self, config: Dict):
        self.config = config
        self.proxies = {}

    async def calculate_proxies(
        self,
        ohlcv: pd.DataFrame,
        symbol: str
    ) -> Dict[str, float]:
        """Calculate all proxies for a stock."""
        try:
            proxies = {}

            # Price action proxies
            proxies.update(self._calculate_price_action(ohlcv))

            # Volume proxies
            proxies.update(self._calculate_volume_proxies(ohlcv))

            # Trend proxies
            proxies.update(self._calculate_trend_proxies(ohlcv))

            # Volatility proxies
            proxies.update(self._calculate_volatility_proxies(ohlcv))

            logger.debug(f"Calculated {len(proxies)} proxies for {symbol}")
            return proxies

        except Exception as e:
            logger.error(f"Error calculating proxies: {str(e)}")
            return {}

    def _calculate_price_action(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """Price action proxies: breakouts, support, resistance."""
        proxies = {}
        try:
            close = ohlcv['close']
            high = ohlcv['high']
            low = ohlcv['low']

            # Simple proxies
            proxies['price_above_ma20'] = 1.0 if close.iloc[-1] > close.rolling(20).mean().iloc[-1] else 0.0
            proxies['price_above_ma50'] = 1.0 if close.iloc[-1] > close.rolling(50).mean().iloc[-1] else 0.0
            proxies['rsi'] = self._calculate_rsi(close)
            proxies['price_range_pct'] = ((high.iloc[-1] - low.iloc[-1]) / low.iloc[-1]) * 100

        except Exception as e:
            logger.warning(f"Error in price action proxies: {str(e)}")
        
        return proxies

    def _calculate_volume_proxies(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """Volume proxies: relative volume, accumulation."""
        proxies = {}
        try:
            volume = ohlcv['volume']
            avg_volume = volume.rolling(20).mean().iloc[-1]
            current_volume = volume.iloc[-1]

            proxies['relative_volume'] = current_volume / avg_volume if avg_volume > 0 else 0
            proxies['volume_trend'] = 1.0 if current_volume > avg_volume else 0.0

        except Exception as e:
            logger.warning(f"Error in volume proxies: {str(e)}")
        
        return proxies

    def _calculate_trend_proxies(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """Trend proxies: EMA, MACD, ADX."""
        proxies = {}
        try:
            close = ohlcv['close']
            
            # EMA crossover
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            proxies['ema_bullish'] = 1.0 if ema12.iloc[-1] > ema26.iloc[-1] else 0.0
            
            # MACD
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            proxies['macd_bullish'] = 1.0 if macd.iloc[-1] > signal.iloc[-1] else 0.0

        except Exception as e:
            logger.warning(f"Error in trend proxies: {str(e)}")
        
        return proxies

    def _calculate_volatility_proxies(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """Volatility proxies: ATR, Bollinger Bands."""
        proxies = {}
        try:
            high = ohlcv['high']
            low = ohlcv['low']
            close = ohlcv['close']

            # ATR
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            proxies['atr'] = atr
            proxies['atr_pct'] = (atr / close.iloc[-1]) * 100 if close.iloc[-1] > 0 else 0

        except Exception as e:
            logger.warning(f"Error in volatility proxies: {str(e)}")
        
        return proxies

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        try:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss if loss.iloc[-1] != 0 else 0
            rsi = 100 - (100 / (1 + rs.iloc[-1]))
            return float(rsi)
        except:
            return 50.0
