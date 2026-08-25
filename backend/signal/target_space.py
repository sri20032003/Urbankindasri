# Target-Space Analysis

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)


class TargetScenario(BaseModel):
    """Target scenario (2x, 3x, 5x)."""
    scenario_name: str  # 2x, 3x, 5x
    target_price: float
    feasibility: str  # FEASIBLE, NOT_FEASIBLE
    feasibility_score: float  # 0-1
    supporting_factors: List[str]
    opposing_factors: List[str]
    historical_frequency_pct: Optional[float] = None
    avg_time_to_achieve_hours: Optional[float] = None


class TargetSpaceOutput(BaseModel):
    """Target space analysis output."""
    scenarios_2x: TargetScenario
    scenarios_3x: TargetScenario
    scenarios_5x: TargetScenario
    recommended_scenarios: List[str]  # Which scenarios to display to user
    target_space_sufficient: bool  # Is there enough room for targets?
    metadata: Dict[str, Any] = {}


class TargetSpaceAnalyzer:
    """Analyze whether target scenarios are feasible."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing TargetSpaceAnalyzer")
    
    async def analyze_target_space(
        self,
        entry_price: float,
        direction: str,  # 'bullish' or 'bearish'
        atr: float,
        volatility_regime: str,
        trend_type: str,
        resistance_levels: Optional[List[float]] = None,
        support_levels: Optional[List[float]] = None,
        historical_volatility: Optional[float] = None,
        momentum_strength: Optional[float] = None
    ) -> TargetSpaceOutput:
        """Analyze feasibility of 2x, 3x, 5x target scenarios.
        
        Args:
            entry_price: Entry price
            direction: bullish or bearish
            atr: Average True Range
            volatility_regime: Current volatility regime
            trend_type: Current trend type
            resistance_levels: Resistance levels (for bullish)
            support_levels: Support levels (for bearish)
            historical_volatility: Historical volatility %
            momentum_strength: Momentum strength (0-1)
        
        Returns:
            TargetSpaceOutput with scenario analysis
        """
        try:
            # Calculate 2x, 3x, 5x prices
            if direction == 'bullish':
                avg_move = atr * 10  # Approximate move
                price_2x = entry_price + (avg_move * 2)
                price_3x = entry_price + (avg_move * 3)
                price_5x = entry_price + (avg_move * 5)
            else:
                avg_move = atr * 10
                price_2x = entry_price - (avg_move * 2)
                price_3x = entry_price - (avg_move * 3)
                price_5x = entry_price - (avg_move * 5)
            
            # Analyze each scenario
            scenario_2x = await self._analyze_scenario(
                entry_price, price_2x, direction, 2.0,
                volatility_regime, trend_type,
                resistance_levels, support_levels,
                momentum_strength
            )
            
            scenario_3x = await self._analyze_scenario(
                entry_price, price_3x, direction, 3.0,
                volatility_regime, trend_type,
                resistance_levels, support_levels,
                momentum_strength
            )
            
            scenario_5x = await self._analyze_scenario(
                entry_price, price_5x, direction, 5.0,
                volatility_regime, trend_type,
                resistance_levels, support_levels,
                momentum_strength
            )
            
            # Determine which scenarios to recommend
            recommended = []
            if scenario_2x.feasibility == 'FEASIBLE':
                recommended.append('2x')
            if scenario_3x.feasibility == 'FEASIBLE':
                recommended.append('3x')
            if scenario_5x.feasibility == 'FEASIBLE':
                recommended.append('5x')
            
            target_space_sufficient = len(recommended) > 0
            
            return TargetSpaceOutput(
                scenarios_2x=scenario_2x,
                scenarios_3x=scenario_3x,
                scenarios_5x=scenario_5x,
                recommended_scenarios=recommended,
                target_space_sufficient=target_space_sufficient,
                metadata={
                    'entry_price': entry_price,
                    'direction': direction,
                    'atr': atr,
                    'volatility_regime': volatility_regime,
                    'trend_type': trend_type,
                    'momentum_strength': momentum_strength
                }
            )
        
        except Exception as e:
            logger.error(f"Error analyzing target space: {str(e)}")
            return self._create_default_target_space()
    
    async def _analyze_scenario(
        self,
        entry_price: float,
        target_price: float,
        direction: str,
        multiplier: float,
        volatility_regime: str,
        trend_type: str,
        resistance_levels: Optional[List[float]],
        support_levels: Optional[List[float]],
        momentum_strength: Optional[float]
    ) -> TargetScenario:
        """Analyze a specific target scenario."""
        
        supporting_factors = []
        opposing_factors = []
        
        # Check trend support
        if trend_type in ['strong_uptrend', 'uptrend'] and direction == 'bullish':
            supporting_factors.append("Strong uptrend supports move")
        elif trend_type in ['strong_downtrend', 'downtrend'] and direction == 'bearish':
            supporting_factors.append("Strong downtrend supports move")
        else:
            opposing_factors.append("Trend not in favor of direction")
        
        # Check volatility
        if volatility_regime in ['high_volatility', 'extreme_volatility']:
            supporting_factors.append("High volatility enables larger moves")
        elif volatility_regime == 'low_volatility':
            opposing_factors.append("Low volatility may limit move")
        
        # Check momentum
        if momentum_strength and momentum_strength > 0.7:
            supporting_factors.append("Strong momentum supports move")
        elif momentum_strength and momentum_strength < 0.3:
            opposing_factors.append("Weak momentum opposes move")
        
        # Check price levels
        if direction == 'bullish':
            if resistance_levels:
                resistances_above = [r for r in resistance_levels if r > entry_price]
                if len(resistances_above) > multiplier:
                    supporting_factors.append(f"Multiple resistances beyond target")
                else:
                    opposing_factors.append(f"Limited room - resistances block move")
        else:
            if support_levels:
                supports_below = [s for s in support_levels if s < entry_price]
                if len(supports_below) > multiplier:
                    supporting_factors.append(f"Multiple supports beyond target")
                else:
                    opposing_factors.append(f"Limited room - supports block move")
        
        # Determine feasibility
        feasibility_score = (
            len(supporting_factors) * 0.25 -
            len(opposing_factors) * 0.25
        )
        feasibility_score = max(0.0, min(1.0, 0.5 + feasibility_score))
        
        if multiplier <= 2.0:
            feasibility_threshold = 0.4  # 2x is easier to achieve
        elif multiplier <= 3.0:
            feasibility_threshold = 0.5  # 3x is moderate
        else:
            feasibility_threshold = 0.6  # 5x is harder
        
        feasibility = 'FEASIBLE' if feasibility_score >= feasibility_threshold else 'NOT_FEASIBLE'
        
        return TargetScenario(
            scenario_name=f"{multiplier:.0f}x",
            target_price=target_price,
            feasibility=feasibility,
            feasibility_score=feasibility_score,
            supporting_factors=supporting_factors,
            opposing_factors=opposing_factors,
            historical_frequency_pct=(feasibility_score * 100) if feasibility == 'FEASIBLE' else 0
        )
    
    def _create_default_target_space(self) -> TargetSpaceOutput:
        """Create default target space output."""
        return TargetSpaceOutput(
            scenarios_2x=TargetScenario(
                scenario_name="2x",
                target_price=0.0,
                feasibility="NOT_FEASIBLE",
                feasibility_score=0.0,
                supporting_factors=[],
                opposing_factors=["Insufficient data"]
            ),
            scenarios_3x=TargetScenario(
                scenario_name="3x",
                target_price=0.0,
                feasibility="NOT_FEASIBLE",
                feasibility_score=0.0,
                supporting_factors=[],
                opposing_factors=["Insufficient data"]
            ),
            scenarios_5x=TargetScenario(
                scenario_name="5x",
                target_price=0.0,
                feasibility="NOT_FEASIBLE",
                feasibility_score=0.0,
                supporting_factors=[],
                opposing_factors=["Insufficient data"]
            ),
            recommended_scenarios=[],
            target_space_sufficient=False
        )
