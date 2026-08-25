"""
Magnitude feasibility engine for 12-20% intraday moves.
Evaluates whether large moves are realistic given current conditions.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class MagnitudeFeasibility:
    """Output for magnitude feasibility analysis."""
    stock_symbol: str
    p_5pct: float  # Probability of +5% move
    p_8pct: float
    p_12pct: float
    p_15pct: float
    p_18pct: float
    p_20pct: float
    
    p_neg3pct: float  # Probability of -3% move
    p_neg5pct: float
    p_neg8pct: float
    
    avg_intraday_range: float  # Historical average intraday range %
    current_atr_pct: float
    volatility_expansion_ratio: float  # Current ATR / Avg ATR
    
    available_target_space_pct: float  # Distance to next resistance
    support_distance_pct: float
    
    is_12pct_feasible: bool
    is_15pct_feasible: bool
    is_18pct_feasible: bool
    is_20pct_feasible: bool
    
    feasibility_reason: str  # Explanation of feasibility

class MagnitudeFeasibilityEngine:
    """Evaluate feasibility of large intraday moves."""
    
    def __init__(self):
        self.min_feasibility_threshold = 0.05  # At least 5% probability for 12% to be feasible
    
    def analyze_magnitude_feasibility(self, 
                                     stock_symbol: str,
                                     current_price: float,
                                     historical_data: pd.DataFrame,
                                     current_atr: float,
                                     support: float,
                                     resistance: float,
                                     catalyst_strength: float = 0.5) -> MagnitudeFeasibility:
        """
        Analyze if 12-20% moves are feasible for this stock.
        
        Args:
            stock_symbol: Stock ticker
            current_price: Current price
            historical_data: Historical OHLCV data
            current_atr: Current Average True Range
            support: Support level
            resistance: Resistance level
            catalyst_strength: 0-1 scale of how strong the catalyst is
        
        Returns:
            MagnitudeFeasibility with detailed analysis
        """
        
        # Calculate historical intraday range
        avg_intraday_range = self._calculate_avg_intraday_range(historical_data)
        avg_atr = historical_data['atr'].mean() if 'atr' in historical_data.columns else current_atr
        
        # Calculate volatility expansion
        volatility_expansion = current_atr / avg_atr if avg_atr > 0 else 1.0
        current_atr_pct = (current_atr / current_price) * 100
        
        # Calculate target space
        available_target_space = resistance - current_price
        available_target_space_pct = (available_target_space / current_price) * 100
        support_distance_pct = (current_price - support) / current_price * 100
        
        # Calculate move probabilities
        p_5pct = self._estimate_move_probability(0.05, avg_intraday_range, volatility_expansion, catalyst_strength)
        p_8pct = self._estimate_move_probability(0.08, avg_intraday_range, volatility_expansion, catalyst_strength)
        p_12pct = self._estimate_move_probability(0.12, avg_intraday_range, volatility_expansion, catalyst_strength)
        p_15pct = self._estimate_move_probability(0.15, avg_intraday_range, volatility_expansion, catalyst_strength)
        p_18pct = self._estimate_move_probability(0.18, avg_intraday_range, volatility_expansion, catalyst_strength)
        p_20pct = self._estimate_move_probability(0.20, avg_intraday_range, volatility_expansion, catalyst_strength)
        
        # Downside probabilities
        p_neg3pct = self._estimate_move_probability(0.03, avg_intraday_range, volatility_expansion, catalyst_strength * 0.7)
        p_neg5pct = self._estimate_move_probability(0.05, avg_intraday_range, volatility_expansion, catalyst_strength * 0.7)
        p_neg8pct = self._estimate_move_probability(0.08, avg_intraday_range, volatility_expansion, catalyst_strength * 0.7)
        
        # Feasibility determination
        is_12pct_feasible = (
            p_12pct >= self.min_feasibility_threshold and 
            available_target_space_pct >= 12
        )
        is_15pct_feasible = (
            p_15pct >= self.min_feasibility_threshold and 
            available_target_space_pct >= 15
        )
        is_18pct_feasible = (
            p_18pct >= self.min_feasibility_threshold and 
            available_target_space_pct >= 18
        )
        is_20pct_feasible = (
            p_20pct >= self.min_feasibility_threshold and 
            available_target_space_pct >= 20
        )
        
        # Generate feasibility reason
        feasibility_reason = self._generate_feasibility_reason(
            p_12pct, available_target_space_pct, volatility_expansion, catalyst_strength
        )
        
        return MagnitudeFeasibility(
            stock_symbol=stock_symbol,
            p_5pct=p_5pct,
            p_8pct=p_8pct,
            p_12pct=p_12pct,
            p_15pct=p_15pct,
            p_18pct=p_18pct,
            p_20pct=p_20pct,
            p_neg3pct=p_neg3pct,
            p_neg5pct=p_neg5pct,
            p_neg8pct=p_neg8pct,
            avg_intraday_range=avg_intraday_range,
            current_atr_pct=current_atr_pct,
            volatility_expansion_ratio=volatility_expansion,
            available_target_space_pct=available_target_space_pct,
            support_distance_pct=support_distance_pct,
            is_12pct_feasible=is_12pct_feasible,
            is_15pct_feasible=is_15pct_feasible,
            is_18pct_feasible=is_18pct_feasible,
            is_20pct_feasible=is_20pct_feasible,
            feasibility_reason=feasibility_reason
        )
    
    def _calculate_avg_intraday_range(self, historical_data: pd.DataFrame) -> float:
        """Calculate average intraday range as percentage."""
        if historical_data.empty or 'high' not in historical_data.columns:
            return 2.0  # Default 2%
        
        intraday_ranges = (historical_data['high'] - historical_data['low']) / historical_data['low'] * 100
        return intraday_ranges.mean()
    
    def _estimate_move_probability(self, target_move: float, avg_range: float, 
                                   volatility_expansion: float, catalyst_strength: float) -> float:
        """
        Estimate probability of achieving target move.
        
        Uses normal distribution assumption with adjustments for:
        - Volatility expansion
        - Catalyst strength
        
        Args:
            target_move: Target move as decimal (0.12 = 12%)
            avg_range: Average intraday range as percentage
            volatility_expansion: Current ATR / Avg ATR
            catalyst_strength: 0-1 scale of catalyst importance
        
        Returns:
            Probability as decimal (0-1)
        """
        # Base probability from normal distribution
        # Simplified: P(X > target) assuming normal distribution
        sigma = (avg_range / 100) * volatility_expansion
        
        if sigma == 0:
            return 0.0
        
        # Z-score
        z_score = target_move / sigma
        
        # Approximate cumulative normal distribution
        # P(Z > z_score) using error function approximation
        from scipy.stats import norm
        try:
            base_prob = 1 - norm.cdf(z_score)
        except:
            base_prob = 0.05 if z_score > 2 else 0.1
        
        # Adjust for catalyst strength
        catalyst_multiplier = 1.0 + (catalyst_strength * 0.5)  # Up to 1.5x if strong catalyst
        
        adjusted_prob = base_prob * catalyst_multiplier
        
        # Cap at reasonable limits
        return min(adjusted_prob, 0.5)
    
    def _generate_feasibility_reason(self, p_12pct: float, available_space: float, 
                                     vol_expansion: float, catalyst_strength: float) -> str:
        """Generate explanation for feasibility determination."""
        reasons = []
        
        if p_12pct < 0.05:
            reasons.append("Low probability of 12% move based on volatility")
        elif p_12pct < 0.15:
            reasons.append("Moderate probability of 12% move")
        else:
            reasons.append(f"High probability ({p_12pct*100:.1f}%) of 12% move")
        
        if available_space < 12:
            reasons.append(f"Limited target space ({available_space:.1f}% to resistance)")
        else:
            reasons.append(f"Adequate target space ({available_space:.1f}% to resistance)")
        
        if vol_expansion > 1.5:
            reasons.append(f"Volatility expanded {vol_expansion:.1f}x historical levels")
        elif vol_expansion < 0.7:
            reasons.append("Volatility compressed, limiting move potential")
        
        if catalyst_strength > 0.7:
            reasons.append("Strong catalyst supporting move")
        
        return "; ".join(reasons)
