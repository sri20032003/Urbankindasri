# Prediction Output & Fusion

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalAction(str, Enum):
    """Trading signal actions."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WAIT = "wait"
    NO_TRADE = "no_trade"


class PredictionFusionOutput(BaseModel):
    """Fused prediction from all models and proxies."""
    symbol: str
    timestamp: datetime
    
    # Direction & Confidence
    direction_probability: float  # 0-1, probability of upside (0.5 = neutral)
    primary_action: SignalAction
    confidence_level: str  # LOW, MEDIUM, HIGH
    
    # Model Outputs
    ml_direction_probability: Optional[float] = None
    ml_confidence: Optional[float] = None
    rl_recommended_action: Optional[str] = None
    rl_confidence: Optional[float] = None
    
    # Proxy Inputs
    technical_proxies_bullish: int = 0
    technical_proxies_bearish: int = 0
    volume_proxies_bullish: int = 0
    volume_proxies_bearish: int = 0
    
    # Regime & Market Context
    market_regime: str
    volatility_regime: str
    trend_type: str
    
    # Signal Quality
    signal_quality_score: float  # 0-100
    model_agreement_score: float  # 0-100
    
    # Entry/Stop/Target
    entry_price_low: Optional[float] = None
    entry_price_high: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price_1: Optional[float] = None
    target_price_2: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    # Validity & Expiration
    signal_valid: bool = True
    signal_valid_until: Optional[datetime] = None
    signal_validity_minutes: int = 60
    
    # Explanation
    top_supporting_factors: List[str] = []
    top_risk_factors: List[str] = []
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class ModelAgreementScorer:
    """Calculate agreement between different models and proxies."""
    
    def __init__(self):
        self.proxy_count = 0
        self.bullish_votes = 0
        self.bearish_votes = 0
        self.neutral_votes = 0
        logger.info("Initializing ModelAgreementScorer")
    
    def add_proxy_vote(
        self,
        direction: str,  # bullish, bearish, neutral
        strength: float,  # 0-1, strength of signal
        reliability: float  # 0-1, historical reliability
    ):
        """Add a proxy vote to agreement calculation.
        
        Args:
            direction: bullish, bearish, or neutral
            strength: Signal strength (0-1)
            reliability: Proxy reliability (0-1)
        """
        # Weight vote by strength and reliability
        weight = strength * reliability
        
        if direction.lower() == 'bullish':
            self.bullish_votes += weight
        elif direction.lower() == 'bearish':
            self.bearish_votes += weight
        else:
            self.neutral_votes += weight
        
        self.proxy_count += 1
    
    def calculate_agreement(self) -> Dict[str, float]:
        """Calculate overall agreement score.
        
        Returns:
            Dict with:
            - agreement_score: 0-100, overall agreement
            - bullish_consensus: % of votes for bullish
            - bearish_consensus: % of votes for bearish
            - direction_probability: 0-1
        """
        total_votes = self.bullish_votes + self.bearish_votes + self.neutral_votes
        
        if total_votes == 0:
            return {
                'agreement_score': 50,
                'bullish_consensus': 0.5,
                'bearish_consensus': 0.5,
                'direction_probability': 0.5
            }
        
        bullish_pct = self.bullish_votes / total_votes
        bearish_pct = self.bearish_votes / total_votes
        
        # Agreement score: how concentrated are votes?
        # 100 = unanimous, 50 = 50-50 split
        max_consensus = max(bullish_pct, bearish_pct, self.neutral_votes / total_votes)
        agreement_score = 50 + (max_consensus - 0.33) * 75
        
        return {
            'agreement_score': float(agreement_score),
            'bullish_consensus': float(bullish_pct),
            'bearish_consensus': float(bearish_pct),
            'direction_probability': float(bullish_pct)
        }
    
    def reset(self):
        """Reset for new calculation."""
        self.proxy_count = 0
        self.bullish_votes = 0
        self.bearish_votes = 0
        self.neutral_votes = 0
