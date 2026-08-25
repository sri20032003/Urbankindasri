# Main Signal Generator

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .quality_scorer import SignalQualityScorer, SignalQualityOutput
from .entry_optimizer import EntryOptimizer, EntryOutput
from .stop_loss_optimizer import StopLossOptimizer, StopLossOutput
from .target_optimizer import TargetOptimizer, TargetOutput
from .target_space import TargetSpaceAnalyzer, TargetSpaceOutput
from .risk_reward import RiskRewardCalculator, RiskRewardOutput
from backend.models import PredictionFusionOutput, SignalAction

logger = logging.getLogger(__name__)


class TradeSignalOutput(BaseModel):
    """Complete trade signal output."""
    symbol: str
    timestamp: datetime
    
    # Action
    action: SignalAction
    
    # Entry/Stop/Target
    entry: EntryOutput
    stop_loss: StopLossOutput
    targets: Dict[int, TargetOutput]  # T1, T2, T3
    
    # Risk/Reward
    risk_reward: RiskRewardOutput
    
    # Quality
    signal_quality: SignalQualityOutput
    target_space: TargetSpaceOutput
    
    # Validity
    signal_valid_until: datetime
    signal_validity_minutes: int
    
    # Explanation
    thesis: str
    top_supporting_factors: List[str]
    top_risk_factors: List[str]
    
    # Metadata
    selected_strategy: str
    model_agreement_score: float
    confidence_level: str
    uncertainty_level: str
    metadata: Dict[str, Any] = {}


class SignalGenerator:
    """Main signal generation engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.quality_scorer = SignalQualityScorer(config)
        self.entry_optimizer = EntryOptimizer(config)
        self.stop_loss_optimizer = StopLossOptimizer(config)
        self.target_optimizer = TargetOptimizer(config)
        self.target_space_analyzer = TargetSpaceAnalyzer(config)
        self.risk_reward_calculator = RiskRewardCalculator(config)
        
        logger.info("Initializing SignalGenerator")
    
    async def generate_signal(
        self,
        prediction: PredictionFusionOutput,
        technical_proxies: Dict[str, Any],
        volume_data: Dict[str, Any],
        momentum_data: Dict[str, Any],
        ohlcv_data: List,
        atr: float,
        vwap: Optional[float],
        support_levels: Optional[List[float]],
        resistance_levels: Optional[List[float]],
        volatility_regime: str,
        liquidity: float,
        event_risk: str,
        sector_analysis: Dict[str, Any] = None,
        market_context: Dict[str, Any] = None
    ) -> Optional[TradeSignalOutput]:
        """Generate complete trade signal.
        
        Args:
            prediction: ML/RL prediction output
            technical_proxies: Technical proxy scores
            volume_data: Volume analysis
            momentum_data: Momentum analysis
            ohlcv_data: OHLCV data
            atr: Average True Range
            vwap: VWAP level
            support_levels: Support levels
            resistance_levels: Resistance levels
            volatility_regime: Volatility regime
            liquidity: Liquidity score (0-1)
            event_risk: Event risk level
            sector_analysis: Sector analysis (optional)
            market_context: Market context (optional)
        
        Returns:
            TradeSignalOutput or None if signal quality too low
        """
        try:
            # Step 1: Calculate signal quality
            quality_output = await self.quality_scorer.calculate_quality(
                technical_proxies=technical_proxies,
                volume_data=volume_data,
                momentum_data=momentum_data,
                ml_output=prediction.metadata.get('ml_output', {}),
                rl_output=prediction.metadata.get('rl_output', {}),
                sector_analysis=sector_analysis or {},
                market_context=market_context or {},
                model_agreement=prediction.model_agreement_score,
                uncertainty_level=self._estimate_uncertainty(prediction),
                event_risk=event_risk,
                liquidity=liquidity,
                risk_reward_ratio=2.0  # Placeholder
            )
            
            # NO-TRADE gate: Check if quality is sufficient
            if not prediction.signal_valid or quality_output.final_quality_score < self.config.get('min_signal_quality', 70):
                logger.info(f"Signal rejected: Quality score {quality_output.final_quality_score} below threshold")
                return None
            
            # Determine direction for entry/stop/target
            direction = 'bullish' if prediction.direction_probability > 0.5 else 'bearish'
            
            # Step 2: Optimize entry point
            entry = await self.entry_optimizer.optimize_entry(
                ohlcv=ohlcv_data,
                direction=direction,
                market_regime=prediction.market_regime,
                atr=atr,
                vwap=vwap,
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
            # Step 3: Optimize stop-loss
            recent_low = min(c.low for c in ohlcv_data[-10:]) if len(ohlcv_data) >= 10 else ohlcv_data[-1].low
            recent_high = max(c.high for c in ohlcv_data[-10:]) if len(ohlcv_data) >= 10 else ohlcv_data[-1].high
            
            stop_loss = await self.stop_loss_optimizer.optimize_stop_loss(
                entry_price=entry.ideal_entry,
                direction=direction,
                atr=atr,
                recent_low=recent_low if direction == 'bullish' else None,
                recent_high=recent_high if direction == 'bearish' else None,
                volatility_percentile=self._get_volatility_percentile(volatility_regime),
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
            # Step 4: Optimize targets
            targets = await self.target_optimizer.optimize_targets(
                entry_price=entry.ideal_entry,
                direction=direction,
                stop_loss_price=stop_loss.stop_loss_price,
                atr=atr,
                resistance_levels=resistance_levels,
                support_levels=support_levels
            )
            
            # Step 5: Analyze target space (2x, 3x, 5x scenarios)
            target_space = await self.target_space_analyzer.analyze_target_space(
                entry_price=entry.ideal_entry,
                direction=direction,
                atr=atr,
                volatility_regime=volatility_regime,
                trend_type=prediction.trend_type,
                resistance_levels=resistance_levels,
                support_levels=support_levels,
                momentum_strength=momentum_data.get('momentum_value')
            )
            
            # Step 6: Calculate risk/reward (use T2 as primary target)
            risk_reward = await self.risk_reward_calculator.calculate_risk_reward(
                entry_price=entry.ideal_entry,
                stop_loss_price=stop_loss.stop_loss_price,
                target_price=targets[2].target_price,
                direction=direction,
                probability_of_target=targets[2].probability,
                account_risk_pct=self.config.get('account_risk_pct', 1.0),
                volatility=self._get_volatility_value(volatility_regime)
            )
            
            # Step 7: Build complete signal
            signal = TradeSignalOutput(
                symbol=prediction.symbol,
                timestamp=datetime.now(),
                action=prediction.primary_action,
                entry=entry,
                stop_loss=stop_loss,
                targets=targets,
                risk_reward=risk_reward,
                signal_quality=quality_output,
                target_space=target_space,
                signal_valid_until=prediction.signal_valid_until,
                signal_validity_minutes=prediction.signal_validity_minutes,
                thesis=self._build_thesis(prediction, entry, stop_loss, targets, direction),
                top_supporting_factors=prediction.top_supporting_factors,
                top_risk_factors=self._extract_risk_factors(quality_output, target_space),
                selected_strategy=self._determine_strategy(technical_proxies),
                model_agreement_score=prediction.model_agreement_score,
                confidence_level=prediction.confidence_level,
                uncertainty_level=self._estimate_uncertainty(prediction),
                metadata={
                    'entry_probability': entry.entry_probability,
                    'recommended_scenarios': target_space.recommended_scenarios,
                    'liquidity_score': liquidity,
                    'event_risk': event_risk
                }
            )
            
            logger.info(f"Signal generated: {prediction.symbol} {direction.upper()} (Quality: {quality_output.final_quality_score:.0f})")
            return signal
        
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}", exc_info=True)
            return None
    
    def _estimate_uncertainty(self, prediction: PredictionFusionOutput) -> str:
        """Estimate uncertainty level from prediction."""
        if prediction.model_agreement_score < 60:
            return "HIGH"
        elif prediction.model_agreement_score < 75:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_volatility_percentile(self, regime: str) -> float:
        """Convert volatility regime to percentile."""
        mapping = {
            'low_volatility': 25.0,
            'normal_volatility': 50.0,
            'high_volatility': 75.0,
            'extreme_volatility': 95.0
        }
        return mapping.get(regime, 50.0)
    
    def _get_volatility_value(self, regime: str) -> float:
        """Convert volatility regime to percentage value."""
        mapping = {
            'low_volatility': 1.0,
            'normal_volatility': 2.0,
            'high_volatility': 3.5,
            'extreme_volatility': 5.0
        }
        return mapping.get(regime, 2.0)
    
    def _build_thesis(self, prediction, entry, stop_loss, targets, direction):
        """Build trading thesis."""
        return (
            f"{direction.upper()} setup: Entry at {entry.ideal_entry:.2f}, "
            f"Stop at {stop_loss.stop_loss_price:.2f}, "
            f"T1 at {targets[1].target_price:.2f}, "
            f"R:R {targets[2].risk_reward_ratio:.1f}:1"
        )
    
    def _extract_risk_factors(self, quality, target_space):
        """Extract top risk factors."""
        factors = []
        
        # From uncertainty
        if quality.breakdown.uncertainty_penalty > 10:
            factors.append("High uncertainty in models")
        
        # From event risk
        if quality.breakdown.event_risk_penalty > 10:
            factors.append("Upcoming event risk")
        
        # From target space
        if not target_space.target_space_sufficient:
            factors.append("Limited target space")
        
        return factors[:3]
    
    def _determine_strategy(self, technical_proxies):
        """Determine selected strategy name."""
        # Placeholder: In production, track which proxies are most active
        return "ML + Volume + Regime + Technical"
