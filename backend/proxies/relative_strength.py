# Relative Strength Engine

import logging
from typing import Dict, Any, List, Optional
from .base_proxy import BaseProxy, ProxyOutput, ProxyDirection, ProxyStrength, ProxyReliability
import numpy as np

logger = logging.getLogger(__name__)


class RelativeStrengthProxy(BaseProxy):
    """Relative Strength - Stock vs NIFTY/Sector proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate relative strength.
        
        Data required:
        - stock_ohlcv: Stock OHLCV data
        - benchmark_ohlcv: Index/Sector OHLCV data (NIFTY/Sector)
        - period: Lookback period (default 20)
        """
        try:
            required = ['stock_ohlcv', 'benchmark_ohlcv']
            if not self._validate_data(data, required):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE,
                    confidence=0.0
                )
            
            stock_ohlcv = data['stock_ohlcv']
            benchmark_ohlcv = data['benchmark_ohlcv']
            period = data.get('period', 20)
            
            if len(stock_ohlcv) < period or len(benchmark_ohlcv) < period:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            # Calculate returns
            stock_closes = np.array([c.close for c in stock_ohlcv[-period:]])
            benchmark_closes = np.array([c.close for c in benchmark_ohlcv[-period:]])
            
            # Returns over period
            stock_return = ((stock_closes[-1] - stock_closes[0]) / stock_closes[0] * 100) if stock_closes[0] > 0 else 0
            benchmark_return = ((benchmark_closes[-1] - benchmark_closes[0]) / benchmark_closes[0] * 100) if benchmark_closes[0] > 0 else 0
            
            # Relative return
            relative_return = stock_return - benchmark_return
            
            # Outperformance ratio
            outperformance_ratio = stock_return / benchmark_return if benchmark_return != 0 else 1.0
            
            # Determine direction and strength
            if relative_return > 2:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.VERY_STRONG if relative_return > 5 else ProxyStrength.STRONG
                confidence = min(0.90, 0.4 + relative_return / 15)
            elif relative_return > 0:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.MODERATE
                confidence = 0.65
            elif relative_return < -2:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.VERY_STRONG if relative_return < -5 else ProxyStrength.STRONG
                confidence = min(0.90, 0.4 + abs(relative_return) / 15)
            elif relative_return < 0:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.MODERATE
                confidence = 0.65
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.WEAK
                confidence = 0.3
            
            return self._create_output(
                value=outperformance_ratio,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.78,
                regime_suitability=0.82,
                metadata={
                    'stock_return': stock_return,
                    'benchmark_return': benchmark_return,
                    'relative_return': relative_return,
                    'outperformance_ratio': outperformance_ratio,
                    'outperforming': outperformance_ratio > 1.05
                }
            )
        
        except Exception as e:
            logger.error(f"Error in RelativeStrengthProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )


class SectorMomentumProxy(BaseProxy):
    """Sector Momentum proxy."""
    
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate sector momentum.
        
        Data required:
        - sector_ohlcv: Sector index OHLCV data
        - period: Lookback period (default 20)
        """
        try:
            if not self._validate_data(data, ['sector_ohlcv']):
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    strength=ProxyStrength.NONE
                )
            
            sector_ohlcv = data['sector_ohlcv']
            period = data.get('period', 20)
            
            if len(sector_ohlcv) < period:
                return self._create_output(
                    direction=ProxyDirection.UNKNOWN,
                    confidence=0.1
                )
            
            closes = np.array([c.close for c in sector_ohlcv[-period:]])
            
            # Sector return
            sector_return = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
            
            # Determine direction
            if sector_return > 3:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.STRONG if sector_return > 5 else ProxyStrength.MODERATE
                confidence = min(0.85, 0.4 + sector_return / 20)
            elif sector_return > 0:
                direction = ProxyDirection.BULLISH
                strength = ProxyStrength.WEAK
                confidence = 0.5
            elif sector_return < -3:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.STRONG if sector_return < -5 else ProxyStrength.MODERATE
                confidence = min(0.85, 0.4 + abs(sector_return) / 20)
            elif sector_return < 0:
                direction = ProxyDirection.BEARISH
                strength = ProxyStrength.WEAK
                confidence = 0.5
            else:
                direction = ProxyDirection.NEUTRAL
                strength = ProxyStrength.VERY_WEAK
                confidence = 0.2
            
            return self._create_output(
                value=sector_return,
                direction=direction,
                strength=strength,
                reliability=ProxyReliability.HIGH,
                confidence=confidence,
                historical_usefulness=0.74,
                regime_suitability=0.80,
                metadata={
                    'sector_return': sector_return,
                    'period': period,
                    'sector_strong': sector_return > 3
                }
            )
        
        except Exception as e:
            logger.error(f"Error in SectorMomentumProxy: {str(e)}")
            return self._create_output(
                direction=ProxyDirection.UNKNOWN,
                strength=ProxyStrength.NONE,
                confidence=0.0
            )
