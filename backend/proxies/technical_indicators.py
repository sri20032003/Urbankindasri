# Technical Indicators as Proxies

import logging
from typing import Dict, Any, List
from .base_proxy import BaseProxy, ProxyOutput, ProxyDirection, ProxyStrength, ProxyReliability
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class RSIProxy(BaseProxy):
    """RSI (Relative Strength Index) as proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate RSI indicator.
        
        Data required:
        - ohlcv: List of OHLCV data
        - period: RSI period (default 14)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            period = data.get('period', 14)
            
            if len(ohlcv) < period + 1:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            # Calculate price changes
            closes = np.array([c.close for c in ohlcv])
            deltas = np.diff(closes)
            
            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gain and loss
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            # Calculate RSI
            if avg_loss == 0:
                rsi = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Determine direction and strength based on RSI levels
            if rsi > 70:
                direction = ProxyDirection.BEARISH  # Overbought
                strength = ProxyStrength.STRONG if rsi > 80 else ProxyStrength.MODERATE
                confidence = (rsi - 70) / 30
            elif rsi < 30:
                direction = ProxyDirection.BULLISH  # Oversold
                strength = ProxyStrength.STRONG if rsi < 20 else ProxyStrength.MODERATE
                confidence = (30 - rsi) / 30
            elif rsi > 50:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.WEAK
                confidence = (rsi - 50) / 20
            elif rsi < 50:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.WEAK
                confidence = (50 - rsi) / 20
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.VERY_WEAK
                confidence = 0.1
            
            return self._create_output(
                value=rsi,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=min(0.85, confidence),
                historical_usefulness=0.65,
                regime_suitability=0.6,  # Works better in ranging markets
                metadata={
                    'rsi': rsi,
                    'avg_gain': avg_gain,
                    'avg_loss': avg_loss,
                    'overbought': rsi > 70,
                    'oversold': rsi < 30
                }
            )
        
        except Exception as e:
            logger.error(f"Error in RSIProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class MACDProxy(BaseProxy):
    """MACD (Moving Average Convergence Divergence) as proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate MACD indicator.
        
        Data required:
        - ohlcv: List of OHLCV data
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            if len(ohlcv) < 26:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            closes = np.array([c.close for c in ohlcv])
            
            # Calculate EMAs
            ema_12 = self._calculate_ema(closes, 12)
            ema_26 = self._calculate_ema(closes, 26)
            
            # MACD line
            macd_line = ema_12[-1] - ema_26[-1]
            
            # Signal line (9-period EMA of MACD)
            macd_values = ema_12 - ema_26
            signal_line = self._calculate_ema(macd_values, 9)[-1]
            
            # Histogram
            histogram = macd_line - signal_line
            
            # Determine direction
            if macd_line > signal_line and histogram > 0:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG if histogram > abs(macd_line) * 0.1 else ProxyStrength.MODERATE
                confidence = min(0.85, abs(histogram) / abs(macd_line)) if macd_line != 0 else 0.5
            elif macd_line < signal_line and histogram < 0:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.STRONG if abs(histogram) > abs(macd_line) * 0.1 else ProxyStrength.MODERATE
                confidence = min(0.85, abs(histogram) / abs(macd_line)) if macd_line != 0 else 0.5
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.3
            
            return self._create_output(
                value=macd_line,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.70,
                regime_suitability=0.75,  # Works well in trending markets
                metadata={
                    'macd_line': macd_line,
                    'signal_line': signal_line,
                    'histogram': histogram,
                    'bullish_crossover': macd_line > signal_line
                }
            )
        
        except Exception as e:
            logger.error(f"Error in MACDProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
    
    def _calculate_ema(self, values: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros(len(values))
        multiplier = 2 / (period + 1)
        
        # First EMA is SMA
        ema[period-1] = np.mean(values[:period])
        
        # Calculate rest
        for i in range(period, len(values)):
            ema[i] = (values[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema


class ADXProxy(BaseProxy):
    """ADX (Average Directional Index) as proxy for trend strength."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate ADX indicator.
        
        Data required:
        - ohlcv: List of OHLCV data
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            if len(ohlcv) < 28:  # 14 period + buffer
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            # Simplified ADX calculation
            adx = self._calculate_adx(ohlcv, period=14)
            
            # ADX values: 0-100
            # 0-20: No trend / Weak trend
            # 20-40: Moderate trend
            # 40+: Strong trend
            
            if adx >= 40:
                direction = ProxyDirection.BULLISH  # Strong trend (direction from other proxies)
                strength = ProxyStrength.VERY_STRONG
                confidence = min(0.95, adx / 100)
            elif adx >= 25:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG
                confidence = 0.75
            elif adx >= 20:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.MODERATE
                confidence = 0.5
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.3
            
            return self._create_output(
                value=adx,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.75,
                regime_suitability=0.8,  # Excellent in trending markets
                metadata={
                    'adx': adx,
                    'trend_strength': 'strong' if adx > 40 else 'moderate' if adx > 25 else 'weak',
                    'is_trending': adx > 20
                }
            )
        
        except Exception as e:
            logger.error(f"Error in ADXProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
    
    def _calculate_adx(self, ohlcv: List, period: int = 14) -> float:
        """Calculate ADX (simplified)."""
        if len(ohlcv) < period:
            return 0.0
        
        # Calculate +DM and -DM
        up_moves = []
        down_moves = []
        
        for i in range(1, len(ohlcv)):
            high_diff = ohlcv[i].high - ohlcv[i-1].high
            low_diff = ohlcv[i-1].low - ohlcv[i].low
            
            if high_diff > 0 and high_diff > low_diff:
                up_moves.append(high_diff)
                down_moves.append(0)
            elif low_diff > 0 and low_diff > high_diff:
                up_moves.append(0)
                down_moves.append(low_diff)
            else:
                up_moves.append(0)
                down_moves.append(0)
        
        # Calculate average directional movements
        if len(up_moves) >= period:
            avg_up = np.mean(up_moves[-period:])
            avg_down = np.mean(down_moves[-period:])
            di_up = 100 * avg_up / (avg_up + avg_down) if (avg_up + avg_down) > 0 else 0
            di_down = 100 * avg_down / (avg_up + avg_down) if (avg_up + avg_down) > 0 else 0
            adx = abs(di_up - di_down)
        else:
            adx = 0.0
        
        return adx
