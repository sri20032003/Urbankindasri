# Momentum Engine

import logging
from typing import Dict, Any, List, Tuple
from .base_proxy import BaseProxy, ProxyOutput, ProxyDirection, ProxyStrength, ProxyReliability
import numpy as np

logger = logging.getLogger(__name__)


class MomentumQualityEngine(BaseProxy):
    """Evaluate momentum quality and persistence."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate momentum quality.
        
        Data required:
        - ohlcv: List of OHLCV data
        - lookback_period: Period for momentum (default 10)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            period = data.get('lookback_period', 10)
            
            if len(ohlcv) < period + 5:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            closes = np.array([c.close for c in ohlcv])
            
            # Momentum: current price - price N periods ago
            momentum = closes[-1] - closes[-period]
            momentum_pct = (momentum / closes[-period]) * 100 if closes[-period] > 0 else 0
            
            # Momentum acceleration: recent momentum vs older momentum
            recent_momentum = closes[-1] - closes[-5]
            previous_momentum = closes[-6] - closes[-11] if len(closes) > 11 else closes[-6] - closes[0]
            
            acceleration = recent_momentum - previous_momentum
            
            # Momentum consistency: count of consecutive up days
            up_days = 0
            for i in range(len(closes) - 1, max(len(closes) - period - 1, -1), -1):
                if closes[i] > closes[i-1]:
                    up_days += 1
                else:
                    break
            
            consistency_score = up_days / period
            
            # Determine strength and direction
            if momentum > 0:
                direction = ProxyDirection.BULLISH
                
                if momentum_pct > 5 and acceleration > 0 and consistency_score > 0.6:
                    strength = ProxyStrength.VERY_STRONG
                    confidence = min(0.95, 0.5 + abs(momentum_pct) / 20)
                elif momentum_pct > 2 and acceleration >= 0 and consistency_score > 0.4:
                    strength = ProxyStrength.STRONG
                    confidence = 0.80
                else:
                    strength = ProxyStrength.MODERATE
                    confidence = 0.60
            elif momentum < 0:
                direction = ProxyDirection.BEARISH
                
                if momentum_pct < -5 and acceleration < 0 and consistency_score < 0.4:
                    strength = ProxyStrength.VERY_STRONG
                    confidence = min(0.95, 0.5 + abs(momentum_pct) / 20)
                elif momentum_pct < -2 and acceleration <= 0 and consistency_score < 0.6:
                    strength = ProxyStrength.STRONG
                    confidence = 0.80
                else:
                    strength = ProxyStrength.MODERATE
                    confidence = 0.60
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.2
            
            return self._create_output(
                value=momentum,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.80,
                regime_suitability=0.85,
                metadata={
                    'momentum': momentum,
                    'momentum_pct': momentum_pct,
                    'acceleration': acceleration,
                    'consistency_score': consistency_score,
                    'up_days': up_days,
                    'momentum_quality': 'strong' if strength in [ProxyStrength.VERY_STRONG, ProxyStrength.STRONG] else 'weak'
                }
            )
        
        except Exception as e:
            logger.error(f"Error in MomentumQualityEngine: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class ROCProxy(BaseProxy):
    """Rate of Change (ROC) proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate ROC indicator.
        
        Data required:
        - ohlcv: List of OHLCV data
        - period: ROC period (default 12)
        """
        try:
            if not self._validate_data(data, ['ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            ohlcv = data['ohlcv']
            period = data.get('period', 12)
            
            if len(ohlcv) < period + 1:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            closes = np.array([c.close for c in ohlcv])
            
            # ROC = ((Close - Close N periods ago) / Close N periods ago) * 100
            roc = ((closes[-1] - closes[-period-1]) / closes[-period-1] * 100) if closes[-period-1] != 0 else 0
            
            # Determine direction based on ROC
            if roc > 2:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG if roc > 5 else ProxyStrength.MODERATE
                confidence = min(0.85, 0.3 + roc / 20)
            elif roc < -2:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.STRONG if roc < -5 else ProxyStrength.MODERATE
                confidence = min(0.85, 0.3 + abs(roc) / 20)
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.2
            
            return self._create_output(
                value=roc,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.MODERATE,
                confidence=confidence,
                historical_usefulness=0.70,
                regime_suitability=0.72,
                metadata={
                    'roc': roc,
                    'period': period,
                    'current_price': closes[-1],
                    'past_price': closes[-period-1]
                }
            )
        
        except Exception as e:
            logger.error(f"Error in ROCProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
