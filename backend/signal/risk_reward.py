# Risk/Reward Calculator

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RiskRewardOutput(BaseModel):
    """Risk/Reward calculation output."""
    entry_price: float
    stop_loss_price: float
    target_price: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    expected_value: float  # Risk-adjusted expected value
    probability_of_profit: float  # 0-1, estimated probability of reaching target
    win_loss_ratio: float  # Average win / Average loss
    position_size_ratio: float  # Recommended position size (0-1)
    metadata: Dict[str, Any] = {}


class RiskRewardCalculator:
    """Calculate risk/reward metrics."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing RiskRewardCalculator")
    
    async def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss_price: float,
        target_price: float,
        direction: str,  # 'bullish' or 'bearish'
        probability_of_target: Optional[float] = None,
        account_risk_pct: float = 1.0,
        volatility: Optional[float] = None
    ) -> RiskRewardOutput:
        """Calculate risk/reward metrics.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop-loss price
            target_price: Target price
            direction: bullish or bearish
            probability_of_target: Probability of reaching target (0-1)
            account_risk_pct: % of account to risk per trade
            volatility: Current volatility %
        
        Returns:
            RiskRewardOutput with metrics
        """
        try:
            # Calculate risk and reward amounts
            risk_amount = abs(entry_price - stop_loss_price)
            reward_amount = abs(target_price - entry_price)
            
            # Risk/Reward ratio
            if risk_amount > 0:
                risk_reward_ratio = reward_amount / risk_amount
            else:
                risk_reward_ratio = 0.0
            
            # Probability of target
            if probability_of_target is None:
                # Estimate based on R:R ratio
                if risk_reward_ratio > 3:
                    probability_of_target = 0.35
                elif risk_reward_ratio > 2:
                    probability_of_target = 0.50
                elif risk_reward_ratio > 1:
                    probability_of_target = 0.65
                else:
                    probability_of_target = 0.75
            
            # Expected value = (Win% * Avg_Win) - (Loss% * Avg_Loss)
            prob_loss = 1.0 - probability_of_target
            expected_value = (probability_of_target * reward_amount) - (prob_loss * risk_amount)
            
            # Win/Loss ratio
            if prob_loss > 0:
                win_loss_ratio = (probability_of_target * reward_amount) / (prob_loss * risk_amount)
            else:
                win_loss_ratio = 1.0
            
            # Position sizing based on risk
            if risk_amount > 0 and account_risk_pct > 0:
                # Position size = (Account Risk % / Risk per trade)
                # Simplified: scale by win probability and volatility
                base_position = account_risk_pct / 100.0
                
                # Reduce if low probability
                if probability_of_target < 0.5:
                    base_position *= 0.6
                elif probability_of_target < 0.6:
                    base_position *= 0.8
                
                # Reduce if high volatility
                if volatility and volatility > 3.0:
                    base_position *= 0.7
                
                position_size_ratio = max(0.0, min(1.0, base_position))
            else:
                position_size_ratio = 0.0
            
            # Validate setup
            if risk_reward_ratio < 1.0:
                logger.warning(f"Poor risk/reward ratio: {risk_reward_ratio:.2f}")
            
            return RiskRewardOutput(
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
                risk_amount=risk_amount,
                reward_amount=reward_amount,
                risk_reward_ratio=risk_reward_ratio,
                expected_value=expected_value,
                probability_of_profit=probability_of_target,
                win_loss_ratio=win_loss_ratio,
                position_size_ratio=position_size_ratio,
                metadata={
                    'direction': direction,
                    'account_risk_pct': account_risk_pct,
                    'volatility': volatility,
                    'setup_quality': 'GOOD' if risk_reward_ratio >= 1.5 else 'FAIR' if risk_reward_ratio >= 1.0 else 'POOR'
                }
            )
        
        except Exception as e:
            logger.error(f"Error calculating risk/reward: {str(e)}")
            return self._create_default_risk_reward(entry_price)
    
    def _create_default_risk_reward(self, entry_price: float) -> RiskRewardOutput:
        """Create default risk/reward output."""
        return RiskRewardOutput(
            entry_price=entry_price,
            stop_loss_price=0.0,
            target_price=0.0,
            risk_amount=0.0,
            reward_amount=0.0,
            risk_reward_ratio=1.0,
            expected_value=0.0,
            probability_of_profit=0.5,
            win_loss_ratio=1.0,
            position_size_ratio=0.0
        )
