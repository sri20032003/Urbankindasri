"""
Risk management engine.
Calculates position sizing, stop loss, and validates risk parameters.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class RiskMetrics:
    """Risk management output."""
    atr: float
    atr_pct: float
    suggested_stop_loss: float
    suggested_position_size_pct: float
    risk_per_trade_pct: float
    reward_per_trade_pct: float
    risk_reward_ratio: float
    liquidity_sufficient: bool
    spread_bps: float
    slippage_estimated_bps: float
    execution_feasible: bool

class RiskManagementEngine:
    """Manage risk parameters for trades."""
    
    def __init__(self):
        self.max_risk_per_trade_pct = 2.0  # Max 2% of account per trade
        self.max_position_size_pct = 5.0  # Max 5% of account
        self.min_risk_reward_ratio = 1.5  # Minimum 1.5:1
        self.min_liquidity_score = 70.0  # Min liquidity score 0-100
        self.max_spread_bps = 50  # Max 50 basis points
    
    def calculate_risk_metrics(self,
                             current_price: float,
                             atr: float,
                             volume: float,
                             avg_volume: float,
                             spread_bps: float,
                             target_price: float) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.
        """
        
        atr_pct = (atr / current_price) * 100
        
        # Calculate stop loss
        suggested_stop_loss = current_price - (atr * 1.5)
        
        # Calculate position size
        position_size_pct = self._calculate_position_size(
            current_price, suggested_stop_loss, self.max_risk_per_trade_pct
        )
        
        # Liquidity check
        liquidity_score = self._calculate_liquidity_score(volume, avg_volume, spread_bps)
        liquidity_sufficient = liquidity_score >= self.min_liquidity_score
        
        # Calculate slippage
        slippage_bps = self._estimate_slippage(volume, avg_volume, spread_bps)
        
        # Risk/Reward
        risk = current_price - suggested_stop_loss
        reward = target_price - current_price
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # Execution feasibility
        execution_feasible = (
            liquidity_sufficient and 
            spread_bps <= self.max_spread_bps and
            risk_reward_ratio >= self.min_risk_reward_ratio
        )
        
        return RiskMetrics(
            atr=atr,
            atr_pct=atr_pct,
            suggested_stop_loss=suggested_stop_loss,
            suggested_position_size_pct=position_size_pct,
            risk_per_trade_pct=(risk / current_price) * 100,
            reward_per_trade_pct=(reward / current_price) * 100,
            risk_reward_ratio=risk_reward_ratio,
            liquidity_sufficient=liquidity_sufficient,
            spread_bps=spread_bps,
            slippage_estimated_bps=slippage_bps,
            execution_feasible=execution_feasible
        )
    
    def _calculate_position_size(self, entry: float, stop: float, max_risk_pct: float) -> float:
        """
        Calculate position size based on risk parameters.
        
        Formula: Position Size = (Account Risk / (Entry - Stop)) * 100
        Simplified here as percentage of max risk.
        """
        risk_per_share = entry - stop
        
        if risk_per_share <= 0:
            return 0.5  # Minimum position
        
        # Position size inversely proportional to risk
        position_size = min(max_risk_pct / ((risk_per_share / entry) * 100), self.max_position_size_pct)
        return max(position_size, 0.5)  # Minimum 0.5%
    
    def _calculate_liquidity_score(self, volume: float, avg_volume: float, spread_bps: float) -> float:
        """
        Calculate liquidity score (0-100).
        """
        score = 100.0
        
        # Volume factor
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        if volume_ratio < 1.0:
            score -= (1 - volume_ratio) * 30
        
        # Spread factor
        if spread_bps > 50:
            score -= min((spread_bps - 50) / 50 * 30, 30)
        
        return max(score, 10)
    
    def _estimate_slippage(self, volume: float, avg_volume: float, spread_bps: float) -> float:
        """
        Estimate slippage in basis points.
        """
        # Base slippage is half the spread
        base_slippage = spread_bps / 2
        
        # Add extra for low volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        if volume_ratio < 1.0:
            base_slippage += (1 - volume_ratio) * 10
        
        return base_slippage
