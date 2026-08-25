# Price Action Proxies

import logging
from typing import Dict, Any, List, Optional
from .base_proxy import BaseProxy, ProxyOutput, ProxyDirection, ProxyStrength, ProxyReliability
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HigherHighsHigherLows(BaseProxy):
    """Proxy detecting higher highs and higher lows (uptrend structure)."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate higher highs/lower lows pattern.
        
        Data required:
        - ohlcv: List of OHLCV data (at least 5 candles)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE,
                    confidence=0.0
                )
            
            ohlcv = data['ohlcv']
            if len(ohlcv) < 5:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE,
                    confidence=0.2
                )
            
            # Extract highs and lows
            highs = [candle.high for candle in ohlcv[-10:]]  # Last 10 candles
            lows = [candle.low for candle in ohlcv[-10:]]
            
            # Detect higher highs
            higher_high_count = 0
            higher_low_count = 0
            
            for i in range(1, len(highs)):
                if highs[i] > highs[i-1]:
                    higher_high_count += 1
                if lows[i] > lows[i-1]:
                    higher_low_count += 1
            
            # Calculate uptrend score (0-1)
            uptrend_score = (higher_high_count + higher_low_count) / (len(highs) - 1) / 2
            
            # Detect downtrend (lower lows and lower highs)
            lower_high_count = len(highs) - higher_high_count - 1
            lower_low_count = len(lows) - higher_low_count - 1
            downtrend_score = (lower_high_count + lower_low_count) / (len(highs) - 1) / 2
            
            # Determine direction
            if uptrend_score > 0.6:
                direction = ProxyDirection.BULLISH
                strength = self._score_to_strength(uptrend_score)
            elif downtrend_score > 0.6:
                direction = ProxyDirection.BEARISH
                strength = self._score_to_strength(downtrend_score)
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
            
            confidence = max(uptrend_score, downtrend_score)
            
            return self._create_output(
                value=uptrend_score - downtrend_score,  # +1 to -1 range
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.75,
                metadata={
                    'higher_highs': higher_high_count,
                    'higher_lows': higher_low_count,
                    'lower_highs': lower_high_count,
                    'lower_lows': lower_low_count,
                    'uptrend_score': uptrend_score,
                    'downtrend_score': downtrend_score
                }
            )
        
        except Exception as e:
            logger.error(f"Error in HigherHighsHigherLows: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
    
    def _score_to_strength(self, score: float) -> ProxyStrength:
        """Convert score (0-1) to strength enum."""
        if score >= 0.9:
            return ProxyStrength.VERY_STRONG
        elif score >= 0.7:
            return ProxyStrength.STRONG
        elif score >= 0.5:
            return ProxyStrength.MODERATE
        elif score >= 0.3:
            return ProxyStrength.WEAK
        else:
            return ProxyStrength.VERY_WEAK


class BreakoutProxy(BaseProxy):
    """Proxy detecting breakout patterns."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Detect breakout above/below recent highs/lows.
        
        Data required:
        - ohlcv: List of OHLCV data
        - lookback_period: Number of candles to look back (default 20)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            lookback = data.get('lookback_period', 20)
            
            if len(ohlcv) < lookback + 1:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE,
                    confidence=0.2
                )
            
            # Get lookback range
            lookback_range = ohlcv[-lookback-1:-1]
            current_candle = ohlcv[-1]
            
            # Calculate period high/low
            period_high = max(c.high for c in lookback_range)
            period_low = min(c.low for c in lookback_range)
            
            # Check for breakout
            if current_candle.close > period_high:
                breakout_strength = (current_candle.close - period_high) / period_high
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG if breakout_strength > 0.02 else ProxyStrength.MODERATE
                confidence = min(0.9, 0.5 + breakout_strength * 10)
            elif current_candle.close < period_low:
                breakdown_strength = (period_low - current_candle.close) / period_low
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.STRONG if breakdown_strength > 0.02 else ProxyStrength.MODERATE
                confidence = min(0.9, 0.5 + breakdown_strength * 10)
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.VERY_WEAK
                confidence = 0.3
            
            return self._create_output(
                value=current_candle.close / period_high if current_candle.close > period_high else current_candle.close / period_low,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.80,
                metadata={
                    'period_high': period_high,
                    'period_low': period_low,
                    'current_close': current_candle.close,
                    'breakout_distance_pct': ((current_candle.close - period_high) / period_high * 100) if current_candle.close > period_high else 0
                }
            )
        
        except Exception as e:
            logger.error(f"Error in BreakoutProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class CompressionExpansionProxy(BaseProxy):
    """Proxy detecting compression (volatility squeeze) and expansion."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Detect compression and expansion patterns.
        
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
            if len(ohlcv) < 20:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE,
                    confidence=0.2
                )
            
            # Calculate Average True Range (ATR) as proxy for volatility
            recent_atr = self._calculate_atr(ohlcv[-20:], 14)
            historical_atr = self._calculate_atr(ohlcv[-100:], 14)
            
            # Compression: recent ATR < historical ATR
            compression_ratio = recent_atr / historical_atr if historical_atr > 0 else 1.0
            
            if compression_ratio < 0.7:  # Significant compression
                direction = ProxyDirection.BULLISH  # Compression often precedes breakout
                strength = ProxyStrength.STRONG
                confidence = min(0.85, 1.0 - compression_ratio)
                signal = "Compression detected - breakout likely"
            elif compression_ratio > 1.5:  # Significant expansion
                direction = ProxyDirection.BEARISH  # Or uncertain
                strength = ProxyStrength.MODERATE
                confidence = min(0.75, compression_ratio - 1.0)
                signal = "Expansion detected - volatility increasing"
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.4
                signal = "Normal volatility"
            
            return self._create_output(
                value=compression_ratio,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.70,
                metadata={
                    'recent_atr': recent_atr,
                    'historical_atr': historical_atr,
                    'compression_ratio': compression_ratio,
                    'signal': signal
                }
            )
        
        except Exception as e:
            logger.error(f"Error in CompressionExpansionProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
    
    def _calculate_atr(self, ohlcv: List, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(ohlcv) < period:
            return 0.0
        
        tr_values = []
        for i in range(len(ohlcv)):
            if i == 0:
                tr = ohlcv[i].high - ohlcv[i].low
            else:
                tr = max(
                    ohlcv[i].high - ohlcv[i].low,
                    abs(ohlcv[i].high - ohlcv[i-1].close),
                    abs(ohlcv[i].low - ohlcv[i-1].close)
                )
            tr_values.append(tr)
        
        atr = sum(tr_values[-period:]) / period
        return atr
