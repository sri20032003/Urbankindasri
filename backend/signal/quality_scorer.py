# Signal Quality Scorer

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalQualityBreakdown(BaseModel):
    """Breakdown of signal quality components."""
    technical_score: float  # 0-100
    volume_score: float  # 0-100
    momentum_score: float  # 0-100
    ml_score: float  # 0-100
    rl_score: float  # 0-100
    sector_score: float  # 0-100
    market_score: float  # 0-100
    uncertainty_penalty: float  # 0-100 (subtracted)
    event_risk_penalty: float  # 0-100 (subtracted)
    liquidity_score: float  # 0-100


class SignalQualityOutput(BaseModel):
    """Signal quality score output."""
    final_quality_score: float  # 0-100, FINAL SCORE
    quality_rating: str  # EXCELLENT, GOOD, FAIR, POOR
    breakdown: SignalQualityBreakdown
    confidence_interpretation: str
    recommendation: str  # "Strong BUY", "Weak BUY", "NO TRADE", etc.
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class SignalQualityScorer:
    """Calculate comprehensive signal quality score."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.min_quality_threshold = config.get('min_quality_threshold', 70)
        logger.info("Initializing SignalQualityScorer")
    
    async def calculate_quality(
        self,
        technical_proxies: Dict[str, Any],
        volume_data: Dict[str, Any],
        momentum_data: Dict[str, Any],
        ml_output: Dict[str, Any],
        rl_output: Dict[str, Any],
        sector_analysis: Dict[str, Any],
        market_context: Dict[str, Any],
        model_agreement: float,
        uncertainty_level: str,  # LOW, MEDIUM, HIGH
        event_risk: str,  # LOW, MEDIUM, HIGH
        liquidity: float,  # 0-1
        risk_reward_ratio: float
    ) -> SignalQualityOutput:
        """Calculate overall signal quality.
        
        Args:
            technical_proxies: Technical proxy scores
            volume_data: Volume analysis scores
            momentum_data: Momentum scores
            ml_output: ML model outputs
            rl_output: RL model outputs
            sector_analysis: Sector confirmation scores
            market_context: Market regime and context
            model_agreement: Model agreement score (0-100)
            uncertainty_level: Uncertainty level
            event_risk: Event risk level
            liquidity: Liquidity score (0-1)
            risk_reward_ratio: Risk/reward ratio
        
        Returns:
            SignalQualityOutput with quality score and breakdown
        """
        try:
            # Calculate component scores
            breakdown = SignalQualityBreakdown(
                technical_score=self._score_technical(technical_proxies),
                volume_score=self._score_volume(volume_data),
                momentum_score=self._score_momentum(momentum_data),
                ml_score=self._score_ml(ml_output),
                rl_score=self._score_rl(rl_output),
                sector_score=self._score_sector(sector_analysis),
                market_score=self._score_market(market_context),
                uncertainty_penalty=self._calculate_uncertainty_penalty(uncertainty_level),
                event_risk_penalty=self._calculate_event_risk_penalty(event_risk),
                liquidity_score=self._score_liquidity(liquidity)
            )
            
            # Calculate weighted final score
            weighted_score = (
                (breakdown.technical_score * 0.20) +
                (breakdown.volume_score * 0.15) +
                (breakdown.momentum_score * 0.15) +
                (breakdown.ml_score * 0.15) +
                (breakdown.rl_score * 0.10) +
                (breakdown.sector_score * 0.10) +
                (breakdown.market_score * 0.10) +
                (breakdown.liquidity_score * 0.05)
            )
            
            # Apply penalties
            final_score = weighted_score - breakdown.uncertainty_penalty - breakdown.event_risk_penalty
            final_score = max(0, min(100, final_score))
            
            # Boost if excellent R:R
            if risk_reward_ratio > 3.0:
                final_score = min(100, final_score + 5)
            elif risk_reward_ratio < 1.0:
                final_score = max(0, final_score - 10)
            
            # Determine rating
            if final_score >= 85:
                quality_rating = "EXCELLENT"
            elif final_score >= 75:
                quality_rating = "GOOD"
            elif final_score >= 60:
                quality_rating = "FAIR"
            else:
                quality_rating = "POOR"
            
            # Confidence interpretation
            if final_score >= 85:
                confidence = "Very High - Multiple strong confirmations"
            elif final_score >= 75:
                confidence = "High - Good agreement across models"
            elif final_score >= 60:
                confidence = "Medium - Some uncertainty present"
            else:
                confidence = "Low - Insufficient confirmations or high uncertainty"
            
            # Recommendation
            if final_score >= 85:
                if uncertainty_level == "LOW" and event_risk == "LOW":
                    recommendation = "STRONG ACTION - Execute if entry conditions met"
                else:
                    recommendation = "Good setup with conditions - Monitor"
            elif final_score >= 75:
                recommendation = "Moderate - Consider if entry optimized"
            elif final_score >= 60:
                recommendation = "Weak - Prefer better opportunities"
            else:
                recommendation = "NO TRADE - Insufficient quality"
            
            return SignalQualityOutput(
                final_quality_score=final_score,
                quality_rating=quality_rating,
                breakdown=breakdown,
                confidence_interpretation=confidence,
                recommendation=recommendation,
                timestamp=datetime.now(),
                metadata={
                    'model_agreement': model_agreement,
                    'uncertainty_level': uncertainty_level,
                    'event_risk': event_risk,
                    'risk_reward_ratio': risk_reward_ratio,
                    'meets_threshold': final_score >= self.min_quality_threshold
                }
            )
        
        except Exception as e:
            logger.error(f"Error calculating signal quality: {str(e)}")
            return self._create_default_quality()
    
    def _score_technical(self, technical_proxies: Dict[str, Any]) -> float:
        """Score technical proxies."""
        if not technical_proxies:
            return 50.0
        
        score = 0.0
        count = 0
        
        for key, value in technical_proxies.items():
            if isinstance(value, dict):
                strength = value.get('strength', 0.5)
                score += strength * 100
                count += 1
            elif isinstance(value, (int, float)):
                score += value if 0 <= value <= 100 else 50
                count += 1
        
        return score / count if count > 0 else 50.0
    
    def _score_volume(self, volume_data: Dict[str, Any]) -> float:
        """Score volume analysis."""
        if not volume_data:
            return 50.0
        
        base_score = 50.0
        
        if volume_data.get('volume_trend') == 'expanding':
            base_score += 15
        elif volume_data.get('volume_trend') == 'contracting':
            base_score -= 10
        
        if volume_data.get('breakout_volume', False):
            base_score += 15
        
        if volume_data.get('relative_volume', 0) > 1.5:
            base_score += 10
        
        return max(0, min(100, base_score))
    
    def _score_momentum(self, momentum_data: Dict[str, Any]) -> float:
        """Score momentum analysis."""
        if not momentum_data:
            return 50.0
        
        base_score = 50.0
        
        momentum = momentum_data.get('momentum_value', 0.5)
        if 0 <= momentum <= 1:
            base_score = momentum * 100
        
        if momentum_data.get('momentum_acceleration') > 0:
            base_score += 10
        elif momentum_data.get('momentum_acceleration') < 0:
            base_score -= 10
        
        if momentum_data.get('multi_timeframe_agreement', False):
            base_score += 15
        
        return max(0, min(100, base_score))
    
    def _score_ml(self, ml_output: Dict[str, Any]) -> float:
        """Score ML model output."""
        if not ml_output:
            return 50.0
        
        confidence = ml_output.get('model_confidence', 0.5)
        agreement = ml_output.get('model_agreement', 0.5)
        
        score = (confidence * 0.6 + agreement * 0.4) * 100
        return max(0, min(100, score))
    
    def _score_rl(self, rl_output: Dict[str, Any]) -> float:
        """Score RL model output."""
        if not rl_output:
            return 50.0
        
        confidence = rl_output.get('action_confidence', 0.5)
        expected_sharpe = rl_output.get('expected_sharpe', 0.0)
        
        score = confidence * 100
        if expected_sharpe > 1.0:
            score += 10
        elif expected_sharpe < 0.0:
            score -= 15
        
        return max(0, min(100, score))
    
    def _score_sector(self, sector_analysis: Dict[str, Any]) -> float:
        """Score sector confirmation."""
        if not sector_analysis:
            return 50.0
        
        base_score = 50.0
        
        if sector_analysis.get('sector_momentum') == 'positive':
            base_score += 20
        elif sector_analysis.get('sector_momentum') == 'negative':
            base_score -= 20
        
        if sector_analysis.get('stock_vs_sector') == 'outperforming':
            base_score += 10
        elif sector_analysis.get('stock_vs_sector') == 'underperforming':
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _score_market(self, market_context: Dict[str, Any]) -> float:
        """Score market context and regime."""
        if not market_context:
            return 50.0
        
        base_score = 50.0
        regime = market_context.get('market_regime', 'sideways')
        
        if regime in ['strong_bull', 'strong_bear']:
            base_score += 20
        elif regime in ['weak_bull', 'weak_bear']:
            base_score += 5
        
        breadth = market_context.get('market_breadth', 0.5)
        base_score += (breadth - 0.5) * 20
        
        return max(0, min(100, base_score))
    
    def _score_liquidity(self, liquidity: float) -> float:
        """Score liquidity."""
        if liquidity < 0.3:
            return 30
        elif liquidity < 0.6:
            return 60
        else:
            return 90
    
    def _calculate_uncertainty_penalty(self, uncertainty_level: str) -> float:
        """Calculate uncertainty penalty."""
        penalties = {
            'LOW': 0.0,
            'MEDIUM': 8.0,
            'HIGH': 20.0
        }
        return penalties.get(uncertainty_level, 5.0)
    
    def _calculate_event_risk_penalty(self, event_risk: str) -> float:
        """Calculate event risk penalty."""
        penalties = {
            'LOW': 0.0,
            'MEDIUM': 10.0,
            'HIGH': 25.0
        }
        return penalties.get(event_risk, 5.0)
    
    def _create_default_quality(self) -> SignalQualityOutput:
        """Create default quality output."""
        return SignalQualityOutput(
            final_quality_score=0.0,
            quality_rating="POOR",
            breakdown=SignalQualityBreakdown(
                technical_score=0.0,
                volume_score=0.0,
                momentum_score=0.0,
                ml_score=0.0,
                rl_score=0.0,
                sector_score=0.0,
                market_score=0.0,
                uncertainty_penalty=100.0,
                event_risk_penalty=0.0,
                liquidity_score=0.0
            ),
            confidence_interpretation="No data available",
            recommendation="NO TRADE"
        )
