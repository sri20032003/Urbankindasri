# Entry Point Optimizer

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class EntryType(str, Enum):
    """Types of entry points."""
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    RETEST = "retest"
    VWAP = "vwap"
    SUPPORT = "support"
    MOMENTUM = "momentum"


class EntryOutput(BaseModel):
    """Entry point output."""
    entry_type: EntryType
    entry_price_low: float
    entry_price_high: float
    ideal_entry: float  # Best entry within range
    entry_probability: float  # 0-1, probability of reaching entry
    entry_urgency: str  # IMMEDIATE, HIGH, MEDIUM, LOW
    signal_expiry_minutes: int  # How long to wait for entry
    rationale: str
    metadata: Dict[str, Any] = {}


class EntryOptimizer:
    """Optimize entry points for signals."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing EntryOptimizer")
    
    async def optimize_entry(
        self,
        ohlcv: List,
        direction: str,  # 'bullish' or 'bearish'
        market_regime: str,
        atr: float,
        vwap: Optional[float] = None,
        support_levels: Optional[List[float]] = None,
        resistance_levels: Optional[List[float]] = None
    ) -> EntryOutput:
        """Determine optimal entry point.
        
        Args:
            ohlcv: OHLCV data
            direction: bullish or bearish
            market_regime: Current market regime
            atr: Average True Range value
            vwap: VWAP level (optional)
            support_levels: Support levels (optional)
            resistance_levels: Resistance levels (optional)
        
        Returns:
            EntryOutput with optimal entry parameters
        """
        try:
            if not ohlcv or len(ohlcv) < 5:
                return self._create_default_entry(direction)
            
            current_price = ohlcv[-1].close
            recent_high = max(c.high for c in ohlcv[-10:])
            recent_low = min(c.low for c in ohlcv[-10:])
            
            if direction == 'bullish':
                entry = await self._bullish_entry(
                    current_price, recent_high, recent_low, atr, vwap,
                    support_levels, resistance_levels, market_regime
                )
            else:
                entry = await self._bearish_entry(
                    current_price, recent_high, recent_low, atr, vwap,
                    support_levels, resistance_levels, market_regime
                )
            
            return entry
        
        except Exception as e:
            logger.error(f"Error optimizing entry: {str(e)}")
            return self._create_default_entry(direction)
    
    async def _bullish_entry(
        self,
        current_price: float,
        recent_high: float,
        recent_low: float,
        atr: float,
        vwap: Optional[float],
        support_levels: Optional[List[float]],
        resistance_levels: Optional[List[float]],
        market_regime: str
    ) -> EntryOutput:
        """Determine bullish entry point."""
        
        # Strategy 1: Breakout above recent high
        breakout_entry = recent_high + (atr * 0.1)  # Slightly above
        
        # Strategy 2: Pullback to VWAP or support
        pullback_entry = None
        if vwap:
            pullback_entry = vwap
        elif support_levels and len(support_levels) > 0:
            pullback_entry = max(support_levels)
        
        # Strategy 3: Retest of recent low + recovery
        retest_entry = recent_low + (atr * 0.05)
        
        # Choose entry based on market regime and proximity
        if current_price > recent_high:
            # Already above, use breakout confirmation
            entry_type = EntryType.BREAKOUT
            entry_low = recent_high
            entry_high = recent_high + (atr * 0.5)
            ideal = recent_high + (atr * 0.2)
            urgency = "IMMEDIATE"
            probability = 0.85
        elif current_price > vwap if vwap else False:
            # At VWAP, good entry
            entry_type = EntryType.VWAP
            entry_low = (vwap * 0.99) if vwap else current_price - atr
            entry_high = (vwap * 1.01) if vwap else current_price + atr
            ideal = vwap or current_price
            urgency = "HIGH"
            probability = 0.80
        elif pullback_entry and current_price > pullback_entry * 0.95:
            # Near pullback level
            entry_type = EntryType.PULLBACK
            entry_low = pullback_entry * 0.98
            entry_high = pullback_entry * 1.02
            ideal = pullback_entry
            urgency = "MEDIUM"
            probability = 0.75
        else:
            # At support, strong entry
            entry_type = EntryType.SUPPORT
            entry_low = current_price - (atr * 0.2)
            entry_high = current_price + (atr * 0.1)
            ideal = current_price
            urgency = "LOW"
            probability = 0.70
        
        signal_expiry = 60 if urgency == "IMMEDIATE" else 120 if urgency == "HIGH" else 240
        
        return EntryOutput(
            entry_type=entry_type,
            entry_price_low=entry_low,
            entry_price_high=entry_high,
            ideal_entry=ideal,
            entry_probability=probability,
            entry_urgency=urgency,
            signal_expiry_minutes=signal_expiry,
            rationale=f"{entry_type.value.capitalize()} entry at {ideal:.2f}",
            metadata={
                'current_price': current_price,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'atr': atr
            }
        )
    
    async def _bearish_entry(
        self,
        current_price: float,
        recent_high: float,
        recent_low: float,
        atr: float,
        vwap: Optional[float],
        support_levels: Optional[List[float]],
        resistance_levels: Optional[List[float]],
        market_regime: str
    ) -> EntryOutput:
        """Determine bearish entry point."""
        
        # Strategy 1: Breakdown below recent low
        breakdown_entry = recent_low - (atr * 0.1)
        
        # Strategy 2: Rally to resistance or VWAP
        rally_entry = None
        if vwap:
            rally_entry = vwap
        elif resistance_levels and len(resistance_levels) > 0:
            rally_entry = min(resistance_levels)
        
        # Choose entry based on market regime
        if current_price < recent_low:
            # Already below, use breakdown confirmation
            entry_type = EntryType.BREAKOUT
            entry_low = recent_low - (atr * 0.5)
            entry_high = recent_low
            ideal = recent_low - (atr * 0.2)
            urgency = "IMMEDIATE"
            probability = 0.85
        elif current_price < vwap if vwap else False:
            # At VWAP, good entry
            entry_type = EntryType.VWAP
            entry_low = (vwap * 0.99) if vwap else current_price - atr
            entry_high = (vwap * 1.01) if vwap else current_price + atr
            ideal = vwap or current_price
            urgency = "HIGH"
            probability = 0.80
        elif rally_entry and current_price < rally_entry * 1.05:
            # Near rally level
            entry_type = EntryType.PULLBACK
            entry_low = rally_entry * 0.98
            entry_high = rally_entry * 1.02
            ideal = rally_entry
            urgency = "MEDIUM"
            probability = 0.75
        else:
            # At resistance, strong entry
            entry_type = EntryType.RESISTANCE
            entry_low = current_price - (atr * 0.1)
            entry_high = current_price + (atr * 0.2)
            ideal = current_price
            urgency = "LOW"
            probability = 0.70
        
        signal_expiry = 60 if urgency == "IMMEDIATE" else 120 if urgency == "HIGH" else 240
        
        return EntryOutput(
            entry_type=entry_type,
            entry_price_low=entry_low,
            entry_price_high=entry_high,
            ideal_entry=ideal,
            entry_probability=probability,
            entry_urgency=urgency,
            signal_expiry_minutes=signal_expiry,
            rationale=f"{entry_type.value.capitalize()} entry at {ideal:.2f}",
            metadata={
                'current_price': current_price,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'atr': atr
            }
        )
    
    def _create_default_entry(self, direction: str) -> EntryOutput:
        """Create default entry output."""
        return EntryOutput(
            entry_type=EntryType.MOMENTUM,
            entry_price_low=0.0,
            entry_price_high=0.0,
            ideal_entry=0.0,
            entry_probability=0.5,
            entry_urgency="LOW",
            signal_expiry_minutes=240,
            rationale="Default entry - insufficient data"
        )
