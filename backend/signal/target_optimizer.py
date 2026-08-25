# Target Optimizer

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)


class TargetOutput(BaseModel):
    """Target output."""
    target_price: float
    target_distance_pct: float
    resistance_level: Optional[float] = None
    probability: float  # 0-1, historical probability of reaching
    expected_time_hours: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    rationale: str
    metadata: Dict[str, Any] = {}


class TargetOptimizer:
    """Optimize target placement."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing TargetOptimizer")
    
    async def optimize_targets(
        self,
        entry_price: float,
        direction: str,  # 'bullish' or 'bearish'
        stop_loss_price: float,
        atr: float,
        resistance_levels: Optional[List[float]] = None,
        support_levels: Optional[List[float]] = None,
        historical_moves: Optional[Dict[str, float]] = None
    ) -> Dict[int, TargetOutput]:
        """Determine optimal targets (T1, T2, T3).
        
        Args:
            entry_price: Entry price
            direction: bullish or bearish
            stop_loss_price: Stop-loss price
            atr: Average True Range
            resistance_levels: Resistance levels (for bullish)
            support_levels: Support levels (for bearish)
            historical_moves: Historical move distribution
        
        Returns:
            Dict with targets: {1: TargetOutput, 2: TargetOutput, 3: TargetOutput}
        """
        try:
            risk = abs(entry_price - stop_loss_price)
            
            if direction == 'bullish':
                targets = await self._bullish_targets(
                    entry_price, risk, atr, resistance_levels,
                    historical_moves
                )
            else:
                targets = await self._bearish_targets(
                    entry_price, risk, atr, support_levels,
                    historical_moves
                )
            
            return targets
        
        except Exception as e:
            logger.error(f"Error optimizing targets: {str(e)}")
            return self._create_default_targets(entry_price, direction, stop_loss_price)
    
    async def _bullish_targets(
        self,
        entry_price: float,
        risk: float,
        atr: float,
        resistance_levels: Optional[List[float]],
        historical_moves: Optional[Dict[str, float]]
    ) -> Dict[int, TargetOutput]:
        """Calculate bullish targets."""
        targets = {}
        
        # Target 1: 1:1 risk-reward (conservative)
        t1_price = entry_price + risk
        if resistance_levels and len(resistance_levels) > 0:
            # Align with first resistance
            nearest_resistance = min([r for r in resistance_levels if r > entry_price],
                                     key=lambda x: abs(x - t1_price),
                                     default=t1_price)
            t1_price = nearest_resistance
        
        targets[1] = TargetOutput(
            target_price=t1_price,
            target_distance_pct=((t1_price - entry_price) / entry_price) * 100,
            resistance_level=t1_price,
            probability=0.85,
            expected_time_hours=4,
            risk_reward_ratio=1.0,
            rationale=f"Conservative T1 at {t1_price:.2f} (1:1 R:R)",
            metadata={'target_type': 'conservative'}
        )
        
        # Target 2: 2.8:1 risk-reward (aggressive)
        t2_price = entry_price + (risk * 2.8)
        if resistance_levels and len(resistance_levels) > 1:
            # Align with second resistance
            higher_resistances = [r for r in resistance_levels if r > t1_price]
            if higher_resistances:
                t2_price = min(higher_resistances, key=lambda x: abs(x - t2_price))
        
        targets[2] = TargetOutput(
            target_price=t2_price,
            target_distance_pct=((t2_price - entry_price) / entry_price) * 100,
            resistance_level=t2_price,
            probability=0.65,
            expected_time_hours=8,
            risk_reward_ratio=2.8,
            rationale=f"Aggressive T2 at {t2_price:.2f} (2.8:1 R:R)",
            metadata={'target_type': 'aggressive'}
        )
        
        # Target 3: 5:1 risk-reward (if feasible)
        t3_price = entry_price + (risk * 5.0)
        if resistance_levels and len(resistance_levels) > 2:
            highest_resistance = max(resistance_levels)
            if highest_resistance > t2_price:
                t3_price = highest_resistance
        
        targets[3] = TargetOutput(
            target_price=t3_price,
            target_distance_pct=((t3_price - entry_price) / entry_price) * 100,
            resistance_level=t3_price,
            probability=0.35,
            expected_time_hours=16,
            risk_reward_ratio=5.0,
            rationale=f"Extended T3 at {t3_price:.2f} (5:1 R:R) - if setup holds",
            metadata={'target_type': 'extended'}
        )
        
        return targets
    
    async def _bearish_targets(
        self,
        entry_price: float,
        risk: float,
        atr: float,
        support_levels: Optional[List[float]],
        historical_moves: Optional[Dict[str, float]]
    ) -> Dict[int, TargetOutput]:
        """Calculate bearish targets."""
        targets = {}
        
        # Target 1: 1:1 risk-reward
        t1_price = entry_price - risk
        if support_levels and len(support_levels) > 0:
            nearest_support = min([s for s in support_levels if s < entry_price],
                                  key=lambda x: abs(x - t1_price),
                                  default=t1_price)
            t1_price = nearest_support
        
        targets[1] = TargetOutput(
            target_price=t1_price,
            target_distance_pct=((entry_price - t1_price) / entry_price) * 100,
            resistance_level=t1_price,
            probability=0.85,
            expected_time_hours=4,
            risk_reward_ratio=1.0,
            rationale=f"Conservative T1 at {t1_price:.2f} (1:1 R:R)",
            metadata={'target_type': 'conservative'}
        )
        
        # Target 2: 2.8:1 risk-reward
        t2_price = entry_price - (risk * 2.8)
        if support_levels and len(support_levels) > 1:
            lower_supports = [s for s in support_levels if s < t1_price]
            if lower_supports:
                t2_price = max(lower_supports, key=lambda x: abs(x - t2_price))
        
        targets[2] = TargetOutput(
            target_price=t2_price,
            target_distance_pct=((entry_price - t2_price) / entry_price) * 100,
            resistance_level=t2_price,
            probability=0.65,
            expected_time_hours=8,
            risk_reward_ratio=2.8,
            rationale=f"Aggressive T2 at {t2_price:.2f} (2.8:1 R:R)",
            metadata={'target_type': 'aggressive'}
        )
        
        # Target 3: 5:1 risk-reward
        t3_price = entry_price - (risk * 5.0)
        if support_levels and len(support_levels) > 2:
            lowest_support = min(support_levels)
            if lowest_support < t2_price:
                t3_price = lowest_support
        
        targets[3] = TargetOutput(
            target_price=t3_price,
            target_distance_pct=((entry_price - t3_price) / entry_price) * 100,
            resistance_level=t3_price,
            probability=0.35,
            expected_time_hours=16,
            risk_reward_ratio=5.0,
            rationale=f"Extended T3 at {t3_price:.2f} (5:1 R:R) - if setup holds",
            metadata={'target_type': 'extended'}
        )
        
        return targets
    
    def _create_default_targets(
        self,
        entry_price: float,
        direction: str,
        stop_loss_price: float
    ) -> Dict[int, TargetOutput]:
        """Create default targets."""
        risk = abs(entry_price - stop_loss_price)
        targets = {}
        
        if direction == 'bullish':
            targets[1] = TargetOutput(
                target_price=entry_price + risk,
                target_distance_pct=(risk / entry_price) * 100,
                probability=0.8,
                risk_reward_ratio=1.0,
                rationale="Default T1"
            )
            targets[2] = TargetOutput(
                target_price=entry_price + (risk * 2),
                target_distance_pct=(risk * 2 / entry_price) * 100,
                probability=0.6,
                risk_reward_ratio=2.0,
                rationale="Default T2"
            )
        else:
            targets[1] = TargetOutput(
                target_price=entry_price - risk,
                target_distance_pct=(risk / entry_price) * 100,
                probability=0.8,
                risk_reward_ratio=1.0,
                rationale="Default T1"
            )
            targets[2] = TargetOutput(
                target_price=entry_price - (risk * 2),
                target_distance_pct=(risk * 2 / entry_price) * 100,
                probability=0.6,
                risk_reward_ratio=2.0,
                rationale="Default T2"
            )
        
        return targets
