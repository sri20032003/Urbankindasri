"""SignalGenerator - Complete signal generation pipeline"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trade signals with quality scoring and risk management."""

    def __init__(self, config: Dict):
        self.config = config
        self.min_quality = config.get('min_signal_quality', 70)
        self.min_confidence = config.get('min_confidence', 0.60)

    async def generate_signal(
        self,
        symbol: str,
        ohlcv,
        indicators: Dict,
        regime: Dict,
        proxies: Dict = None
    ) -> Optional[Dict]:
        """Generate a trade signal."""
        try:
            # Determine action
            action = self._determine_action(indicators, regime)
            
            if not action or action == 'NO_TRADE':
                logger.debug(f"No trade signal for {symbol}")
                return None

            # Calculate entry, stop, target
            entry_zone = self._calculate_entry(ohlcv, indicators)
            stop_loss = self._calculate_stop_loss(ohlcv, indicators)
            targets = self._calculate_targets(ohlcv, entry_zone, indicators)
            
            # Quality scoring
            quality = self._calculate_quality_score(
                action, indicators, regime, proxies
            )
            
            if quality < self.min_quality:
                logger.debug(f"Signal quality {quality} < minimum {self.min_quality}")
                return None

            # Confidence
            confidence = self._calculate_confidence(indicators, regime)
            
            # Risk/Reward
            risk_reward = self._calculate_risk_reward(
                entry_zone, stop_loss, targets
            )

            # Build signal
            signal = {
                'symbol': symbol,
                'action': action,
                'entry_zone': entry_zone,
                'stop_loss': stop_loss,
                'targets': targets,
                'quality': quality,
                'confidence': confidence,
                'risk_reward': risk_reward,
                'regime': regime,
                'timestamp': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(hours=1)).isoformat(),
                'supporting_proxies': self._get_top_proxies(proxies, 5),
                'risks': self._identify_risks(indicators, regime)
            }

            logger.info(f"Generated signal for {symbol}: {action} (quality: {quality})")
            return signal

        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return None

    def _determine_action(self, indicators: Dict, regime: Dict) -> Optional[str]:
        """Determine action: BUY, SELL, HOLD, WAIT, or NO_TRADE."""
        try:
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', {})
            trend = regime.get('trend', 'NEUTRAL')
            
            # Simple logic
            if rsi > 60 and macd.get('histogram', 0) > 0 and 'BULL' in trend:
                return 'BUY'
            elif rsi < 40 and macd.get('histogram', 0) < 0 and 'BEAR' in trend:
                return 'SELL'
            elif 'BULL' in trend:
                return 'HOLD'
            elif 'BEAR' in trend:
                return 'WAIT'
            else:
                return 'NO_TRADE'
        except:
            return 'NO_TRADE'

    def _calculate_entry(self, ohlcv, indicators: Dict) -> float:
        """Calculate entry price."""
        current_price = ohlcv['close'].iloc[-1]
        return round(current_price, 2)

    def _calculate_stop_loss(self, ohlcv, indicators: Dict) -> float:
        """Calculate stop loss (ATR-based)."""
        current_price = ohlcv['close'].iloc[-1]
        atr = indicators.get('atr', 0)
        stop = current_price - (atr * 2)
        return round(stop, 2)

    def _calculate_targets(self, ohlcv, entry: float, indicators: Dict) -> List[float]:
        """Calculate target prices."""
        atr = indicators.get('atr', 0)
        target1 = entry + (atr * 2)
        target2 = entry + (atr * 3)
        target3 = entry + (atr * 5)
        return [
            round(target1, 2),
            round(target2, 2),
            round(target3, 2)
        ]

    def _calculate_quality_score(self, action: str, indicators: Dict, regime: Dict, proxies: Dict = None) -> int:
        """Calculate signal quality (0-100)."""
        score = 50
        
        # RSI contribution
        rsi = indicators.get('rsi', 50)
        if (50 < rsi < 70) or (30 < rsi < 50):
            score += 10
        
        # MACD contribution
        macd = indicators.get('macd', {})
        if macd.get('histogram', 0) != 0:
            score += 10
        
        # Trend confirmation
        if 'BULL' in regime.get('trend', '') or 'BEAR' in regime.get('trend', ''):
            score += 15
        
        # Volatility
        if regime.get('volatility', 'NORMAL') == 'NORMAL':
            score += 10
        
        return min(100, max(0, score))

    def _calculate_confidence(self, indicators: Dict, regime: Dict) -> float:
        """Calculate confidence (0-1)."""
        confidence = 0.5
        
        rsi = indicators.get('rsi', 50)
        if 60 < rsi < 70 or 30 < rsi < 40:
            confidence += 0.15
        
        if 'STRONG' in regime.get('trend', ''):
            confidence += 0.15
        
        return min(1.0, max(0.0, confidence))

    def _calculate_risk_reward(self, entry: float, stop: float, targets: List[float]) -> Dict:
        """Calculate risk/reward ratios."""
        risk = abs(entry - stop)
        return {
            'target1_rr': round(abs(targets[0] - entry) / risk, 2) if risk > 0 else 0,
            'target2_rr': round(abs(targets[1] - entry) / risk, 2) if risk > 0 else 0,
            'target3_rr': round(abs(targets[2] - entry) / risk, 2) if risk > 0 else 0,
        }

    def _get_top_proxies(self, proxies: Dict, count: int) -> List[str]:
        """Get top supporting proxies."""
        if not proxies:
            return []
        # Return sorted by absolute value
        sorted_proxies = sorted(
            proxies.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return [f"{name}: {value}" for name, value in sorted_proxies[:count]]

    def _identify_risks(self, indicators: Dict, regime: Dict) -> List[str]:
        """Identify key risks."""
        risks = []
        
        if regime.get('volatility') == 'HIGH':
            risks.append("High volatility - potential slippage")
        
        if indicators.get('rsi', 50) > 70:
            risks.append("Overbought conditions - potential pullback")
        elif indicators.get('rsi', 50) < 30:
            risks.append("Oversold conditions - potential bounce")
        
        if 'WEAK' in regime.get('trend', ''):
            risks.append("Weak trend - confirmation needed")
        
        return risks[:3]
