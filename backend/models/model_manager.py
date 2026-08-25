# Model Manager

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .ml_ensemble import MLEnsemble, MLPredictionOutput
from .rl_ensemble import RLEnsemble, RLPredictionOutput
from .prediction_output import PredictionFusionOutput, ModelAgreementScorer, SignalAction

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages all ML/RL models and fusion."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ml_ensemble = MLEnsemble(config)
        self.rl_ensemble = RLEnsemble(config)
        self.agreement_scorer = ModelAgreementScorer()
        
        self.last_update = datetime.now()
        self.model_update_interval = timedelta(hours=config.get('model_update_interval_hours', 24))
        
        logger.info("Initializing ModelManager")
    
    async def generate_prediction(
        self,
        symbol: str,
        features: Dict[str, float],
        feature_names: List[str],
        market_state: Dict[str, Any],
        proxy_votes: List[Dict[str, Any]]
    ) -> PredictionFusionOutput:
        """Generate fused prediction from all models.
        
        Args:
            symbol: Stock symbol
            features: Feature dictionary for ML
            feature_names: Feature names in order
            market_state: Current market state (regime, volatility, etc.)
            proxy_votes: List of proxy votes (direction, strength, reliability)
        
        Returns:
            Fused prediction output
        """
        try:
            # Get ML prediction
            ml_pred = await self.ml_ensemble.predict(features, feature_names)
            
            # Get RL prediction
            rl_pred = await self.rl_ensemble.predict(market_state)
            
            # Calculate model agreement
            ml_direction = 'bullish' if ml_pred.direction_probability > 0.6 else 'bearish' if ml_pred.direction_probability < 0.4 else 'neutral'
            rl_direction = 'bullish' if rl_pred.recommended_action == 'BUY' else 'bearish' if rl_pred.recommended_action == 'SELL' else 'neutral'
            
            # Process proxy votes
            self.agreement_scorer.reset()
            
            bullish_proxies = 0
            bearish_proxies = 0
            volume_bullish = 0
            volume_bearish = 0
            
            for vote in proxy_votes:
                direction = vote.get('direction', 'neutral')
                strength = vote.get('strength', 0.5)
                reliability = vote.get('reliability', 0.5)
                proxy_type = vote.get('type', 'technical')
                
                self.agreement_scorer.add_proxy_vote(direction, strength, reliability)
                
                if direction == 'bullish':
                    if proxy_type == 'volume':
                        volume_bullish += 1
                    else:
                        bullish_proxies += 1
                elif direction == 'bearish':
                    if proxy_type == 'volume':
                        volume_bearish += 1
                    else:
                        bearish_proxies += 1
            
            agreement = self.agreement_scorer.calculate_agreement()
            direction_prob = agreement['direction_probability']
            agreement_score = agreement['agreement_score']
            
            # Determine primary action
            if agreement_score > 75 and direction_prob > 0.65:
                primary_action = SignalAction.BUY
                confidence = 'HIGH'
            elif agreement_score > 75 and direction_prob < 0.35:
                primary_action = SignalAction.SELL
                confidence = 'HIGH'
            elif agreement_score > 60 and direction_prob > 0.55:
                primary_action = SignalAction.BUY
                confidence = 'MEDIUM'
            elif agreement_score > 60 and direction_prob < 0.45:
                primary_action = SignalAction.SELL
                confidence = 'MEDIUM'
            elif agreement_score > 50:
                primary_action = SignalAction.WAIT
                confidence = 'MEDIUM'
            else:
                primary_action = SignalAction.NO_TRADE
                confidence = 'LOW'
            
            # Calculate signal quality
            ml_weight = 0.35
            rl_weight = 0.25
            proxy_weight = 0.40
            
            signal_quality = (
                (ml_pred.model_confidence * ml_weight) +
                (rl_pred.action_confidence * rl_weight) +
                ((agreement_score / 100.0) * proxy_weight)
            ) * 100
            
            signal_quality = max(0, min(100, signal_quality))
            
            # Signal validity
            validity_minutes = 60 if confidence == 'HIGH' else 90 if confidence == 'MEDIUM' else 120
            signal_valid_until = datetime.now() + timedelta(minutes=validity_minutes)
            
            return PredictionFusionOutput(
                symbol=symbol,
                timestamp=datetime.now(),
                direction_probability=float(direction_prob),
                primary_action=primary_action,
                confidence_level=confidence,
                ml_direction_probability=ml_pred.direction_probability,
                ml_confidence=ml_pred.model_confidence,
                rl_recommended_action=rl_pred.recommended_action,
                rl_confidence=rl_pred.action_confidence,
                technical_proxies_bullish=bullish_proxies,
                technical_proxies_bearish=bearish_proxies,
                volume_proxies_bullish=volume_bullish,
                volume_proxies_bearish=volume_bearish,
                market_regime=market_state.get('market_regime', 'unknown'),
                volatility_regime=market_state.get('volatility_regime', 'unknown'),
                trend_type=market_state.get('trend_type', 'unknown'),
                signal_quality_score=signal_quality,
                model_agreement_score=agreement_score,
                signal_valid=signal_quality >= self.config.get('min_signal_quality', 70),
                signal_valid_until=signal_valid_until,
                signal_validity_minutes=validity_minutes,
                top_supporting_factors=self._extract_top_factors(
                    proxy_votes, market_state, ml_pred, rl_pred, direction_prob > 0.5
                ),
                metadata={
                    'ml_output': ml_pred.dict(),
                    'rl_output': rl_pred.dict(),
                    'agreement_details': agreement,
                    'proxy_count': len(proxy_votes)
                }
            )
        
        except Exception as e:
            logger.error(f"Error generating prediction: {str(e)}")
            return self._create_default_prediction(symbol)
    
    def _extract_top_factors(
        self,
        proxy_votes: List[Dict[str, Any]],
        market_state: Dict[str, Any],
        ml_pred: MLPredictionOutput,
        rl_pred: RLPredictionOutput,
        bullish_bias: bool
    ) -> List[str]:
        """Extract top supporting factors for the signal."""
        factors = []
        
        # Add ML factor
        if ml_pred.model_confidence > 0.7:
            factors.append(f"ML ensemble confidence: {ml_pred.model_confidence:.0%}")
        
        # Add RL factor
        if rl_pred.action_confidence > 0.7:
            factors.append(f"RL agent agreement: {rl_pred.action_confidence:.0%}")
        
        # Add regime factor
        regime = market_state.get('market_regime', '')
        if regime in ['strong_bull', 'strong_bear']:
            factors.append(f"Strong {regime.replace('_', ' ')} regime")
        
        # Add top proxy factors (by strength)
        strong_proxies = [
            v for v in proxy_votes
            if v.get('strength', 0) > 0.7 and
            ((v.get('direction') == 'bullish' and bullish_bias) or
             (v.get('direction') == 'bearish' and not bullish_bias))
        ]
        
        for proxy in sorted(strong_proxies, key=lambda x: x.get('strength', 0), reverse=True)[:3]:
            factors.append(f"{proxy.get('name', 'Proxy')}: {proxy.get('direction').capitalize()}")
        
        return factors[:5]  # Return top 5 factors
    
    def _create_default_prediction(self, symbol: str) -> PredictionFusionOutput:
        """Create default neutral prediction."""
        return PredictionFusionOutput(
            symbol=symbol,
            timestamp=datetime.now(),
            direction_probability=0.5,
            primary_action=SignalAction.NO_TRADE,
            confidence_level='LOW',
            market_regime='unknown',
            volatility_regime='unknown',
            trend_type='unknown',
            signal_quality_score=0,
            model_agreement_score=50,
            signal_valid=False
        )
    
    async def needs_model_update(self) -> bool:
        """Check if models need retraining."""
        elapsed = datetime.now() - self.last_update
        return elapsed > self.model_update_interval
    
    async def update_models(self):
        """Trigger model retraining (placeholder)."""
        logger.info("Model update triggered")
        # In production, this would retrain models
        self.last_update = datetime.now()
