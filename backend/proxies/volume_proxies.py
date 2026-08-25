# Volume Proxies

import logging
from typing import Dict, Any, List
from .base_proxy import BaseProxy, ProxyOutput, ProxyDirection, ProxyStrength, ProxyReliability
import numpy as np

logger = logging.getLogger(__name__)


class RelativeVolumeProxy(BaseProxy):
    """Relative Volume (RVOL) proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate relative volume compared to average.
        
        Data required:
        - ohlcv: List of OHLCV data
        - lookback_period: Period for average calculation (default 20)
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
                    confidence=0.1
                )
            
            # Current volume
            current_vol = ohlcv[-1].volume
            
            # Average volume (excluding current)
            avg_vol = np.mean([c.volume for c in ohlcv[-lookback-1:-1]])
            
            # Calculate RVOL
            rvol = current_vol / avg_vol if avg_vol > 0 else 1.0
            
            # Determine direction based on price action + volume
            current_price = ohlcv[-1].close
            prev_price = ohlcv[-2].close if len(ohlcv) > 1 else current_price
            
            if rvol > 1.5:
                strength = ProxyStrength.VERY_STRONG
                confidence = min(0.95, (rvol - 1.0) / 2.0)  # Cap at 0.95
                
                if current_price > prev_price:
                    direction = ProxyDirection.BULLISH
                elif current_price < prev_price:
                    direction = ProxyDirection.BEARISH
                else:
                    direction = ProxyDirection.NEUTRAL
            elif rvol > 1.2:
                strength = ProxyStrength.STRONG
                confidence = 0.7
                
                if current_price > prev_price:
                    direction = ProxyDirection.BULLISH
                elif current_price < prev_price:
                    direction = ProxyDirection.BEARISH
                else:
                    direction = ProxyDirection.NEUTRAL
            elif rvol > 0.8:
                strength = ProxyStrength.MODERATE
                confidence = 0.4
                direction = ProxyDirection.NEUTRAL
            else:
                strength = ProxyStrength.WEAK
                confidence = 0.2
                direction = ProxyDirection.NEUTRAL  # Low volume - cautious
            
            return self._create_output(
                value=rvol,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.VERY_HIGH,
                confidence=confidence,
                historical_usefulness=0.82,
                regime_suitability=0.85,
                metadata={
                    'current_volume': current_vol,
                    'average_volume': avg_vol,
                    'rvol': rvol,
                    'volume_spike': rvol > 1.5
                }
            )
        
        except Exception as e:
            logger.error(f"Error in RelativeVolumeProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class OBVProxy(BaseProxy):
    """On-Balance Volume (OBV) proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate OBV indicator.
        
        Data required:
        - ohlcv: List of OHLCV data (at least 10 candles)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            if len(ohlcv) < 10:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            # Calculate OBV
            obv = []
            current_obv = 0
            
            for i, candle in enumerate(ohlcv):
                if i == 0:
                    current_obv = candle.volume
                else:
                    if candle.close > ohlcv[i-1].close:
                        current_obv += candle.volume
                    elif candle.close < ohlcv[i-1].close:
                        current_obv -= candle.volume
                obv.append(current_obv)
            
            # Calculate OBV trend (last 10 vs previous 10)
            recent_obv = obv[-1]
            obv_ema_short = np.mean(obv[-5:])
            obv_ema_long = np.mean(obv[-15:]) if len(obv) >= 15 else np.mean(obv)
            
            # OBV should increase with uptrend and decrease with downtrend
            obv_trend = recent_obv - obv_ema_long
            obv_momentum = obv_ema_short - obv_ema_long
            
            # Price direction
            price_up = ohlcv[-1].close > ohlcv[-2].close if len(ohlcv) > 1 else False
            
            # Check for bullish divergence (price up, OBV up)
            if obv_momentum > 0 and price_up:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG if obv_momentum > abs(obv_ema_long) * 0.1 else ProxyStrength.MODERATE
                confidence = 0.75
            elif obv_momentum < 0 and not price_up:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.STRONG
                confidence = 0.75
            elif obv_momentum > 0:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.MODERATE
                confidence = 0.6
            elif obv_momentum < 0:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.MODERATE
                confidence = 0.6
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.3
            
            return self._create_output(
                value=recent_obv,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.MODERATE,
                confidence=confidence,
                historical_usefulness=0.68,
                regime_suitability=0.70,
                metadata={
                    'obv': recent_obv,
                    'obv_momentum': obv_momentum,
                    'obv_trend': 'up' if obv_momentum > 0 else 'down',
                    'bullish_divergence': obv_momentum > 0 and price_up
                }
            )
        
        except Exception as e:
            logger.error(f"Error in OBVProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class VolumeAccelerationProxy(BaseProxy):
    """Volume Acceleration proxy - detecting increasing volume momentum."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Detect volume acceleration.
        
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
            if len(ohlcv) < 10:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            # Get last 10 volumes
            volumes = [c.volume for c in ohlcv[-10:]]
            
            # Calculate volume trend
            vol_short = np.mean(volumes[-3:])  # Last 3 candles
            vol_medium = np.mean(volumes[-7:]) # Last 7 candles
            vol_long = np.mean(volumes)        # All 10 candles
            
            # Volume acceleration
            short_vs_long = vol_short / vol_long if vol_long > 0 else 1.0
            medium_vs_long = vol_medium / vol_long if vol_long > 0 else 1.0
            
            # If recent volume is increasing significantly
            if short_vs_long > 1.3 and medium_vs_long > 1.1:
                direction = ProxyDirection.BULLISH  # Accelerating volume suggests conviction
                strength = ProxyStrength.VERY_STRONG
                confidence = min(0.9, (short_vs_long - 1.0) / 0.3)
            elif short_vs_long > 1.15 and medium_vs_long > 1.05:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG
                confidence = 0.75
            elif short_vs_long > 0.85 and medium_vs_long > 0.9:
                direction = ProxyDirection.BEARISH  # Declining volume
                strength = ProxyStrength.MODERATE
                confidence = 0.5
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.3
            
            return self._create_output(
                value=short_vs_long,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.76,
                regime_suitability=0.78,
                metadata={
                    'vol_short_3d': vol_short,
                    'vol_medium_7d': vol_medium,
                    'vol_long_10d': vol_long,
                    'acceleration_ratio': short_vs_long,
                    'accelerating': short_vs_long > 1.15
                }
            )
        
        except Exception as e:
            logger.error(f"Error in VolumeAccelerationProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
