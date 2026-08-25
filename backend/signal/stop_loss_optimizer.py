# Stop-Loss Optimizer

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)


class StopLossOutput(BaseModel):
    """Stop-loss output."""
    stop_loss_price: float
    stop_loss_pct: float  # % below entry
    stop_loss_type: str  # ATR-based, structure-based, volatility-adjusted
    max_adverse_excursion_historical: Optional[float] = None
    stop_loss_risk: float  # Risk amount per unit
    rationale: str
    metadata: Dict[str, Any] = {}


class StopLossOptimizer:
    """Optimize stop-loss placement."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing StopLossOptimizer")
    
    async def optimize_stop_loss(
        self,
        entry_price: float,
        direction: str,  # 'bullish' or 'bearish'
        atr: float,
        recent_low: Optional[float] = None,
        recent_high: Optional[float] = None,
        volatility_percentile: float = 50.0,
        support_levels: Optional[List[float]] = None,
        resistance_levels: Optional[List[float]] = None
    ) -> StopLossOutput:
        """Determine optimal stop-loss placement.
        
        Args:
            entry_price: Entry price
            direction: bullish or bearish
            atr: Average True Range
            recent_low: Recent swing low (for bullish)
            recent_high: Recent swing high (for bearish)
            volatility_percentile: Current volatility percentile (0-100)
            support_levels: Support levels (for bullish)
            resistance_levels: Resistance levels (for bearish)
        
        Returns:
            StopLossOutput with optimized stop-loss price
        """
        try:
            if direction == 'bullish':
                stop_loss = await self._bullish_stop_loss(
                    entry_price, atr, recent_low, volatility_percentile,
                    support_levels
                )
            else:
                stop_loss = await self._bearish_stop_loss(
                    entry_price, atr, recent_high, volatility_percentile,
                    resistance_levels
                )
            
            return stop_loss
        
        except Exception as e:
            logger.error(f"Error optimizing stop-loss: {str(e)}")
            return self._create_default_stop_loss(entry_price, direction, atr)
    
    async def _bullish_stop_loss(
        self,
        entry_price: float,
        atr: float,
        recent_low: Optional[float],
        volatility_percentile: float,
        support_levels: Optional[List[float]]
    ) -> StopLossOutput:
        """Calculate bullish stop-loss."""
        
        # Method 1: ATR-based (most common)
        atr_stop = entry_price - (atr * 2.0)  # 2x ATR below entry
        
        # Method 2: Structure-based (use recent low or support)
        structure_stop = None
        if support_levels and len(support_levels) > 0:
            structure_stop = min(support_levels) * 0.99  # Slightly below support
        elif recent_low:
            structure_stop = recent_low * 0.99
        
        # Method 3: Volatility-adjusted
        if volatility_percentile > 75:
            # High volatility: use larger stop
            vol_stop = entry_price - (atr * 2.5)
        elif volatility_percentile < 25:
            # Low volatility: can use tighter stop
            vol_stop = entry_price - (atr * 1.5)
        else:
            # Normal volatility
            vol_stop = entry_price - (atr * 2.0)
        
        # Choose the best stop (usually structure, but not too tight)
        if structure_stop and structure_stop > atr_stop * 0.95:
            final_stop = structure_stop
            stop_type = "structure-based"
        elif volatility_percentile > 75:
            final_stop = vol_stop
            stop_type = "volatility-adjusted (high)"
        else:
            final_stop = atr_stop
            stop_type = "ATR-based"
        
        stop_pct = ((entry_price - final_stop) / entry_price) * 100
        
        return StopLossOutput(
            stop_loss_price=final_stop,
            stop_loss_pct=stop_pct,
            stop_loss_type=stop_type,
            stop_loss_risk=entry_price - final_stop,
            rationale=f"{stop_type.capitalize()} at {final_stop:.2f} ({stop_pct:.2f}% below entry)",
            metadata={
                'atr_stop': atr_stop,
                'structure_stop': structure_stop,
                'vol_stop': vol_stop,
                'atr': atr,
                'volatility_percentile': volatility_percentile
            }
        )
    
    async def _bearish_stop_loss(
        self,
        entry_price: float,
        atr: float,
        recent_high: Optional[float],
        volatility_percentile: float,
        resistance_levels: Optional[List[float]]
    ) -> StopLossOutput:
        """Calculate bearish stop-loss."""
        
        # Method 1: ATR-based
        atr_stop = entry_price + (atr * 2.0)  # 2x ATR above entry
        
        # Method 2: Structure-based
        structure_stop = None
        if resistance_levels and len(resistance_levels) > 0:
            structure_stop = max(resistance_levels) * 1.01  # Slightly above resistance
        elif recent_high:
            structure_stop = recent_high * 1.01
        
        # Method 3: Volatility-adjusted
        if volatility_percentile > 75:
            vol_stop = entry_price + (atr * 2.5)
        elif volatility_percentile < 25:
            vol_stop = entry_price + (atr * 1.5)
        else:
            vol_stop = entry_price + (atr * 2.0)
        
        # Choose the best stop
        if structure_stop and structure_stop < atr_stop * 1.05:
            final_stop = structure_stop
            stop_type = "structure-based"
        elif volatility_percentile > 75:
            final_stop = vol_stop
            stop_type = "volatility-adjusted (high)"
        else:
            final_stop = atr_stop
            stop_type = "ATR-based"
        
        stop_pct = ((final_stop - entry_price) / entry_price) * 100
        
        return StopLossOutput(
            stop_loss_price=final_stop,
            stop_loss_pct=stop_pct,
            stop_loss_type=stop_type,
            stop_loss_risk=final_stop - entry_price,
            rationale=f"{stop_type.capitalize()} at {final_stop:.2f} ({stop_pct:.2f}% above entry)",
            metadata={
                'atr_stop': atr_stop,
                'structure_stop': structure_stop,
                'vol_stop': vol_stop,
                'atr': atr,
                'volatility_percentile': volatility_percentile
            }
        )
    
    def _create_default_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> StopLossOutput:
        """Create default stop-loss."""
        if direction == 'bullish':
            stop = entry_price - (atr * 2.0)
            stop_pct = ((entry_price - stop) / entry_price) * 100
        else:
            stop = entry_price + (atr * 2.0)
            stop_pct = ((stop - entry_price) / entry_price) * 100
        
        return StopLossOutput(
            stop_loss_price=stop,
            stop_loss_pct=stop_pct,
            stop_loss_type="ATR-based",
            stop_loss_risk=abs(stop - entry_price),
            rationale=f"Default ATR-based stop at {stop:.2f}"
        )
