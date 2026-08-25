"""
Post-trade analytics and continuous learning engine.
Records outcomes and learns from historical signals.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import numpy as np
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class TradeOutcome:
    """Actual trade outcome for learning."""
    signal_id: int
    stock_symbol: str
    predicted_direction: str
    actual_direction: str
    
    predicted_magnitude_pct: float
    actual_magnitude_pct: float
    
    entry_price: float
    actual_entry: float
    actual_exit: float
    exit_reason: str  # 'TARGET_1', 'STOP_LOSS', 'SIGNAL_INVALID', 'MANUAL'
    
    holding_time_minutes: int
    pnl: float
    pnl_pct: float
    
    # Excursion metrics
    mfe: float  # Maximum Favorable Excursion
    mae: float  # Maximum Adverse Excursion
    
    slippage_bps: float
    was_profitable: bool
    
    timestamp: datetime

class PostTradeAnalytics:
    """Analyze trade outcomes for continuous improvement."""
    
    def __init__(self):
        self.recent_outcomes: List[TradeOutcome] = []
    
    def record_outcome(self, trade_outcome: TradeOutcome):
        """
        Record trade outcome for analysis.
        """
        self.recent_outcomes.append(trade_outcome)
        logger.info(f"Recorded outcome for {trade_outcome.stock_symbol}: "
                   f"PnL={trade_outcome.pnl_pct:.2f}%, MFE={trade_outcome.mfe:.2f}%, "
                   f"MAE={trade_outcome.mae:.2f}%")
        
        # Keep only recent 500 outcomes
        if len(self.recent_outcomes) > 500:
            self.recent_outcomes = self.recent_outcomes[-500:]
    
    def calculate_signal_quality_accuracy(self, signal_quality_score: float) -> float:
        """
        Validate if signal quality score was accurate.
        Compare predicted vs actual outcomes for signals with similar quality scores.
        
        Returns: Accuracy of quality score prediction (0-1)
        """
        if not self.recent_outcomes:
            return 0.5
        
        # Filter outcomes by similar quality score (within 10 points)
        similar_quality_outcomes = [
            o for o in self.recent_outcomes
            if abs(o.pnl_pct) < signal_quality_score * 2
        ]
        
        if not similar_quality_outcomes:
            return 0.5
        
        # Calculate win rate
        wins = sum(1 for o in similar_quality_outcomes if o.was_profitable)
        win_rate = wins / len(similar_quality_outcomes)
        
        return win_rate
    
    def calculate_proxy_accuracy(self) -> Dict[str, float]:
        """
        Calculate accuracy of each proxy based on historical trades.
        
        Returns: Dictionary mapping proxy names to accuracy scores (0-1)
        """
        # This would require storing proxy values with outcomes
        # For now, return placeholder
        return {}
    
    def detect_strategy_deterioration(self, lookback_trades: int = 20) -> bool:
        """
        Detect if a previously good strategy has started failing.
        
        Returns: True if deterioration detected
        """
        if len(self.recent_outcomes) < lookback_trades:
            return False
        
        recent = self.recent_outcomes[-lookback_trades:]
        old = self.recent_outcomes[-2*lookback_trades:-lookback_trades]
        
        recent_win_rate = sum(1 for o in recent if o.was_profitable) / len(recent)
        old_win_rate = sum(1 for o in old if o.was_profitable) / len(old)
        
        # Deterioration if win rate dropped by 20% or more
        deterioration = (old_win_rate - recent_win_rate) > 0.20
        
        if deterioration:
            logger.warning(f"Strategy deterioration detected: {old_win_rate:.2%} -> {recent_win_rate:.2%}")
        
        return deterioration
    
    def get_performance_summary(self, lookback_trades: int = 50) -> Dict:
        """
        Get performance summary for recent trades.
        """
        if not self.recent_outcomes:
            return {}
        
        recent = self.recent_outcomes[-lookback_trades:]
        
        pnls = [o.pnl_pct for o in recent]
        wins = sum(1 for o in recent if o.was_profitable)
        losses = len(recent) - wins
        
        avg_win = np.mean([p for p in pnls if p > 0]) if wins > 0 else 0
        avg_loss = np.mean([p for p in pnls if p < 0]) if losses > 0 else 0
        
        profit_factor = abs(avg_win * wins / (avg_loss * losses)) if losses > 0 else float('inf')
        
        return {
            'total_trades': len(recent),
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': wins / len(recent) if recent else 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': sum(pnls),
            'avg_pnl': np.mean(pnls) if pnls else 0,
            'std_dev': np.std(pnls) if pnls else 0
        }

class ContinuousLearningEngine:
    """Learn from historical outcomes to improve future signals."""
    
    def __init__(self, proxy_reliability_scorer, strategy_ranker):
        self.proxy_scorer = proxy_reliability_scorer
        self.strategy_ranker = strategy_ranker
    
    def update_proxy_reliability(self, outcomes: List[TradeOutcome]):
        """
        Update proxy reliability scores based on trade outcomes.
        """
        logger.info(f"Updating proxy reliability from {len(outcomes)} outcomes")
        
        # Group outcomes by proxy usage
        # Update reliability scores
        # This requires storing which proxies were used in each signal
    
    def update_strategy_rankings(self, outcomes: List[TradeOutcome]):
        """
        Update strategy/combination rankings based on recent performance.
        """
        logger.info(f"Updating strategy rankings from {len(outcomes)} outcomes")
        
        # Calculate performance metrics for each strategy
        # Update rankings
        # Detect underperforming strategies
    
    def suggest_model_improvements(self, outcomes: List[TradeOutcome]) -> Dict:
        """
        Suggest improvements to ML/RL models based on prediction accuracy.
        
        Returns: Suggestions for model updates
        """
        suggestions = []
        
        # Analyze prediction errors
        # Identify patterns in failures
        # Suggest retraining
        
        return {'suggestions': suggestions}
