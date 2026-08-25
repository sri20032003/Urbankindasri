"""
Signal generation and quality scoring engine.
Implements the NO-TRADE gate and comprehensive signal fusion.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class SignalCard:
    """Final trade signal output."""
    timestamp: datetime
    stock_symbol: str
    
    # Signal decision
    action: str  # BUY, SELL, HOLD, WAIT, NO_TRADE
    confidence: float  # 0-1
    uncertainty: str  # LOW, MEDIUM, HIGH
    signal_quality: float  # 0-100
    live_confirmation: float  # 0-100
    
    # Setup information
    selected_setup: str  # Comma-separated proxy names
    market_regime: str
    volatility_regime: str
    primary_timeframe: str
    confirmation_timeframe: str
    
    # Entry/Stop/Target
    entry_price_low: float
    entry_price_high: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float
    
    # Magnitude scenarios
    is_12pct_feasible: bool
    is_15pct_feasible: bool
    is_18pct_feasible: bool
    is_20pct_feasible: bool
    
    # Risk metrics
    risk: float  # Entry - Stop Loss
    reward: float  # Target 1 - Entry
    risk_reward_ratio: float
    expected_holding_minutes: int
    
    # Model agreement
    model_agreement: float  # 0-1
    ml_probability: float
    
    # Supporting evidence
    top_supporting_proxies: List[str]
    top_risks: List[str]
    
    # Signal lifecycle
    validity_until: datetime
    is_valid: bool
    invalidation_reason: Optional[str] = None
    
    # Explanation
    reasoning: str

class SignalGenerationEngine:
    """Main signal generation orchestrator."""
    
    def __init__(self):
        self.min_signal_quality = 70
        self.min_model_agreement = 0.6
        self.signal_validity_hours = 2
    
    def generate_signal(self,
                       stock_symbol: str,
                       current_price: float,
                       proxy_outputs: List[Dict],
                       market_regime: str,
                       volatility_regime: str,
                       ml_prediction: Dict,
                       magnitude_feasibility: Dict,
                       risk_metrics: Dict) -> SignalCard:
        """
        Generate final trade signal.
        
        Args:
            stock_symbol: Stock ticker
            current_price: Current price
            proxy_outputs: List of proxy outputs
            market_regime: Current market regime
            volatility_regime: Current volatility regime
            ml_prediction: ML ensemble prediction
            magnitude_feasibility: Magnitude feasibility analysis
            risk_metrics: Risk management metrics
        
        Returns:
            SignalCard with complete signal information
        """
        
        timestamp = datetime.utcnow()
        
        # Apply NO-TRADE gate
        no_trade_reason = self._apply_no_trade_gate(
            proxy_outputs, market_regime, ml_prediction, 
            magnitude_feasibility, risk_metrics
        )
        
        if no_trade_reason:
            logger.info(f"NO-TRADE for {stock_symbol}: {no_trade_reason}")
            return SignalCard(
                timestamp=timestamp,
                stock_symbol=stock_symbol,
                action="NO_TRADE",
                confidence=0.0,
                uncertainty="HIGH",
                signal_quality=0.0,
                live_confirmation=0.0,
                selected_setup="",
                market_regime=market_regime,
                volatility_regime=volatility_regime,
                primary_timeframe="5m",
                confirmation_timeframe="15m",
                entry_price_low=current_price,
                entry_price_high=current_price,
                stop_loss=current_price,
                target_1=current_price,
                target_2=current_price,
                target_3=current_price,
                is_12pct_feasible=False,
                is_15pct_feasible=False,
                is_18pct_feasible=False,
                is_20pct_feasible=False,
                risk=0,
                reward=0,
                risk_reward_ratio=0,
                expected_holding_minutes=0,
                model_agreement=0,
                ml_probability=0,
                top_supporting_proxies=[],
                top_risks=[no_trade_reason],
                validity_until=timestamp + timedelta(hours=self.signal_validity_hours),
                is_valid=False,
                invalidation_reason=no_trade_reason,
                reasoning=no_trade_reason
            )
        
        # Calculate signal quality
        signal_quality = self._calculate_signal_quality(
            proxy_outputs, ml_prediction, market_regime, magnitude_feasibility
        )
        
        # Determine action
        action = self._determine_action(
            proxy_outputs, ml_prediction, signal_quality, market_regime
        )
        
        # Get entry/stop/target levels
        entry_low, entry_high = self._calculate_entry_zone(current_price, proxy_outputs)
        stop_loss = self._calculate_stop_loss(current_price, risk_metrics)
        target_1, target_2, target_3 = self._calculate_targets(
            entry_high, current_price, magnitude_feasibility
        )
        
        # Calculate risk/reward
        risk = entry_high - stop_loss
        reward = target_1 - entry_high
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # Get supporting evidence
        top_proxies = self._get_top_supporting_proxies(proxy_outputs, 5)
        top_risks = self._get_top_risks(stock_symbol, risk_metrics)
        
        # Model agreement
        model_agreement = ml_prediction.get('model_agreement', 0)
        ml_probability = ml_prediction.get('direction_probability', 0.5)
        
        # Confidence and uncertainty
        confidence = signal_quality / 100.0
        if confidence > 0.85:
            uncertainty = "LOW"
        elif confidence > 0.70:
            uncertainty = "MEDIUM"
        else:
            uncertainty = "HIGH"
        
        # Generate reasoning
        reasoning = self._generate_signal_reasoning(
            action, signal_quality, top_proxies, market_regime, 
            magnitude_feasibility, risk_reward_ratio
        )
        
        return SignalCard(
            timestamp=timestamp,
            stock_symbol=stock_symbol,
            action=action,
            confidence=confidence,
            uncertainty=uncertainty,
            signal_quality=signal_quality,
            live_confirmation=min(ml_probability * 100, 100),
            selected_setup=",".join(top_proxies),
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            primary_timeframe="5m",
            confirmation_timeframe="15m",
            entry_price_low=entry_low,
            entry_price_high=entry_high,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            is_12pct_feasible=magnitude_feasibility.get('is_12pct_feasible', False),
            is_15pct_feasible=magnitude_feasibility.get('is_15pct_feasible', False),
            is_18pct_feasible=magnitude_feasibility.get('is_18pct_feasible', False),
            is_20pct_feasible=magnitude_feasibility.get('is_20pct_feasible', False),
            risk=risk,
            reward=reward,
            risk_reward_ratio=risk_reward_ratio,
            expected_holding_minutes=int(magnitude_feasibility.get('expected_holding_time', 60)),
            model_agreement=model_agreement,
            ml_probability=ml_probability,
            top_supporting_proxies=top_proxies,
            top_risks=top_risks,
            validity_until=timestamp + timedelta(hours=self.signal_validity_hours),
            is_valid=True,
            reasoning=reasoning
        )
    
    def _apply_no_trade_gate(self, proxy_outputs: List[Dict], market_regime: str,
                            ml_prediction: Dict, magnitude_feasibility: Dict,
                            risk_metrics: Dict) -> Optional[str]:
        """
        Apply NO-TRADE filter. Return reason if should reject signal.
        """
        
        # Check data quality
        if not proxy_outputs or len(proxy_outputs) < 5:
            return "Insufficient proxy data"
        
        # Check market regime
        if market_regime == "TRANSITION":
            return "Market in transition, unclear regime"
        
        # Check ML agreement
        model_agreement = ml_prediction.get('model_agreement', 0)
        if model_agreement < self.min_model_agreement:
            return f"Low model agreement: {model_agreement:.2f}"
        
        # Check target space
        if not magnitude_feasibility.get('is_12pct_feasible', False):
            return "No feasible 12%+ target space"
        
        # Check risk/reward
        if risk_metrics.get('risk_reward_ratio', 0) < 1.5:
            return "Poor risk/reward ratio"
        
        # Check liquidity
        if not risk_metrics.get('liquidity_sufficient', True):
            return "Insufficient liquidity"
        
        return None
    
    def _calculate_signal_quality(self, proxy_outputs: List[Dict], 
                                 ml_prediction: Dict, market_regime: str,
                                 magnitude_feasibility: Dict) -> float:
        """
        Calculate overall signal quality (0-100).
        """
        scores = []
        
        # Proxy strength
        proxy_strengths = [p.get('strength', 0) for p in proxy_outputs if p]
        if proxy_strengths:
            scores.append(np.mean(proxy_strengths) * 100)
        
        # ML prediction confidence
        ml_prob = ml_prediction.get('direction_probability', 0.5)
        ml_confidence = abs(ml_prob - 0.5) * 200  # 0-100
        scores.append(ml_confidence)
        
        # Regime suitability
        if market_regime in ["STRONG_BULL", "STRONG_BEAR"]:
            scores.append(90)
        elif market_regime in ["WEAK_BULL", "WEAK_BEAR"]:
            scores.append(75)
        else:
            scores.append(50)
        
        # Magnitude feasibility
        if magnitude_feasibility.get('is_20pct_feasible', False):
            scores.append(95)
        elif magnitude_feasibility.get('is_15pct_feasible', False):
            scores.append(85)
        elif magnitude_feasibility.get('is_12pct_feasible', False):
            scores.append(75)
        else:
            scores.append(40)
        
        # Calculate weighted average
        quality_score = np.mean(scores) if scores else 0
        return float(min(quality_score, 100))
    
    def _determine_action(self, proxy_outputs: List[Dict], ml_prediction: Dict,
                         signal_quality: float, market_regime: str) -> str:
        """
        Determine final action: BUY, SELL, HOLD, WAIT, NO_TRADE.
        """
        
        if signal_quality < self.min_signal_quality:
            return "WAIT"
        
        ml_prob = ml_prediction.get('direction_probability', 0.5)
        
        if ml_prob > 0.65 and signal_quality > 75:
            return "BUY"
        elif ml_prob < 0.35 and signal_quality > 75:
            return "SELL"
        elif 0.45 <= ml_prob <= 0.55:
            return "HOLD"
        else:
            return "WAIT"
    
    def _calculate_entry_zone(self, current_price: float, proxy_outputs: List[Dict]) -> Tuple[float, float]:
        """
        Calculate entry zone based on proxies.
        """
        # Simplified: entry zone is 0.5% around current price
        zone_width = current_price * 0.005
        entry_low = current_price - zone_width
        entry_high = current_price + zone_width
        
        return entry_low, entry_high
    
    def _calculate_stop_loss(self, current_price: float, risk_metrics: Dict) -> float:
        """
        Calculate stop loss level.
        """
        atr = risk_metrics.get('atr', current_price * 0.02)
        stop_loss = current_price - (atr * 1.5)
        
        return max(stop_loss, current_price * 0.95)  # Don't go below 5% from entry
    
    def _calculate_targets(self, entry_price: float, current_price: float, 
                          magnitude_feasibility: Dict) -> Tuple[float, float, float]:
        """
        Calculate target levels.
        """
        target_space = magnitude_feasibility.get('available_target_space_pct', 15)
        
        # Conservative targets
        target_1 = entry_price * (1 + min(target_space * 0.4, 0.08))  # 40% of space or 8%, whichever is less
        target_2 = entry_price * (1 + min(target_space * 0.7, 0.12))  # 70% of space or 12%
        target_3 = entry_price * (1 + min(target_space, 0.20))  # Full space or 20%
        
        return target_1, target_2, target_3
    
    def _get_top_supporting_proxies(self, proxy_outputs: List[Dict], limit: int = 5) -> List[str]:
        """
        Get top supporting proxies by strength.
        """
        sorted_proxies = sorted(
            [p for p in proxy_outputs if p],
            key=lambda x: x.get('strength', 0),
            reverse=True
        )
        
        return [p.get('name', 'unknown') for p in sorted_proxies[:limit]]
    
    def _get_top_risks(self, stock_symbol: str, risk_metrics: Dict) -> List[str]:
        """
        Get top risk factors.
        """
        risks = []
        
        if risk_metrics.get('volatility_high', False):
            risks.append("High volatility")
        
        if risk_metrics.get('liquidity_low', False):
            risks.append("Low liquidity")
        
        if risk_metrics.get('resistance_near', False):
            risks.append("Resistance nearby")
        
        if risk_metrics.get('news_event_risk', False):
            risks.append("Event risk")
        
        return risks[:3]
    
    def _generate_signal_reasoning(self, action: str, quality: float,
                                  top_proxies: List[str], market_regime: str,
                                  magnitude_feasibility: Dict,
                                  risk_reward: float) -> str:
        """
        Generate human-readable reasoning for signal.
        """
        reasoning_parts = []
        
        reasoning_parts.append(f"Signal Quality: {quality:.0f}/100")
        
        if top_proxies:
            reasoning_parts.append(f"Key Proxies: {', '.join(top_proxies[:3])}")
        
        reasoning_parts.append(f"Regime: {market_regime}")
        
        if magnitude_feasibility.get('is_15pct_feasible', False):
            reasoning_parts.append("15%+ move feasible")
        elif magnitude_feasibility.get('is_12pct_feasible', False):
            reasoning_parts.append("12%+ move feasible")
        
        if risk_reward > 2:
            reasoning_parts.append(f"Excellent R:R {risk_reward:.1f}:1")
        elif risk_reward > 1.5:
            reasoning_parts.append(f"Good R:R {risk_reward:.1f}:1")
        
        return " | ".join(reasoning_parts)
