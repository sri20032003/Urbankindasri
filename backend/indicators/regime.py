"""RegimeDetector - Market and volatility regime classification"""
import logging
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class RegimeDetector:
    """Detects market regimes (bullish, bearish, sideways, etc.)."""

    def __init__(self, config: Dict):
        self.config = config

    async def detect_regime(
        self,
        ohlcv: pd.DataFrame,
        indicators: Dict
    ) -> Dict[str, str]:
        """Detect current market regime."""
        try:
            regime = {}

            # Trend regime
            regime['trend'] = self._detect_trend(ohlcv, indicators)

            # Volatility regime
            regime['volatility'] = self._detect_volatility(ohlcv, indicators)

            # Momentum regime
            regime['momentum'] = self._detect_momentum(indicators)

            logger.debug(f"Detected regime: {regime}")
            return regime

        except Exception as e:
            logger.error(f"Error detecting regime: {str(e)}")
            return {'trend': 'NEUTRAL', 'volatility': 'NORMAL', 'momentum': 'NEUTRAL'}

    def _detect_trend(self, ohlcv: pd.DataFrame, indicators: Dict) -> str:
        """Detect trend regime: STRONG_BULL, WEAK_BULL, NEUTRAL, WEAK_BEAR, STRONG_BEAR."""
        try:
            close = ohlcv['close']
            sma50 = indicators.get('sma50', close.rolling(50).mean().iloc[-1])
            sma200 = indicators.get('sma200', close.rolling(200).mean().iloc[-1])
            adx = indicators.get('adx', 25)
            
            current_price = close.iloc[-1]
            
            if current_price > sma50 > sma200 and adx > 40:
                return 'STRONG_BULL'
            elif current_price > sma50 > sma200:
                return 'WEAK_BULL'
            elif current_price < sma50 < sma200 and adx > 40:
                return 'STRONG_BEAR'
            elif current_price < sma50 < sma200:
                return 'WEAK_BEAR'
            else:
                return 'NEUTRAL'
        except:
            return 'NEUTRAL'

    def _detect_volatility(self, ohlcv: pd.DataFrame, indicators: Dict) -> str:
        """Detect volatility regime: LOW, NORMAL, HIGH, EXTREME."""
        try:
            atr_pct = (indicators.get('atr', 0) / ohlcv['close'].iloc[-1]) * 100
            
            if atr_pct < 1:
                return 'LOW'
            elif atr_pct < 2:
                return 'NORMAL'
            elif atr_pct < 3:
                return 'HIGH'
            else:
                return 'EXTREME'
        except:
            return 'NORMAL'

    def _detect_momentum(self, indicators: Dict) -> str:
        """Detect momentum regime: STRONG_UP, WEAK_UP, NEUTRAL, WEAK_DOWN, STRONG_DOWN."""
        try:
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', {})
            macd_hist = macd.get('histogram', 0)
            
            if rsi > 70 and macd_hist > 0:
                return 'STRONG_UP'
            elif rsi > 50 and macd_hist > 0:
                return 'WEAK_UP'
            elif rsi < 30 and macd_hist < 0:
                return 'STRONG_DOWN'
            elif rsi < 50 and macd_hist < 0:
                return 'WEAK_DOWN'
            else:
                return 'NEUTRAL'
        except:
            return 'NEUTRAL'
