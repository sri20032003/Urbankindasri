# Market Regime Detection

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketRegimeType(str, Enum):
    """Market regime classification."""
    STRONG_BULL = "strong_bull"
    WEAK_BULL = "weak_bull"
    SIDEWAYS = "sideways"
    WEAK_BEAR = "weak_bear"
    STRONG_BEAR = "strong_bear"


class VolatilityRegimeType(str, Enum):
    """Volatility regime classification."""
    LOW_VOLATILITY = "low_volatility"
    NORMAL_VOLATILITY = "normal_volatility"
    HIGH_VOLATILITY = "high_volatility"
    EXTREME_VOLATILITY = "extreme_volatility"


class TrendType(str, Enum):
    """Trend classification."""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    RANGE = "range"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


class RegimeOutput(BaseModel):
    """Market regime output."""
    market_regime: MarketRegimeType
    volatility_regime: VolatilityRegimeType
    trend_type: TrendType
    regime_strength: float  # 0-1, how strong is current regime
    regime_probability: float  # 0-1, confidence in regime classification
    atr_percentile: float  # 0-100, ATR as percentile of historical
    vix_reading: Optional[float] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class MarketRegimeDetector:
    """Detect current market regime."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        logger.info("Initializing MarketRegimeDetector")
    
    async def detect_regime(
        self,
        nifty_ohlcv: List,
        bank_nifty_ohlcv: Optional[List] = None,
        vix_value: Optional[float] = None
    ) -> RegimeOutput:
        """Detect current market regime.
        
        Args:
            nifty_ohlcv: NIFTY index OHLCV data
            bank_nifty_ohlcv: BANK NIFTY data (optional)
            vix_value: India VIX reading (optional)
        
        Returns:
            RegimeOutput with regime classification
        """
        try:
            if not nifty_ohlcv or len(nifty_ohlcv) < 50:
                logger.warning("Insufficient NIFTY data for regime detection")
                return self._create_default_regime()
            
            # Detect trend
            trend_type = self._detect_trend(nifty_ohlcv)
            
            # Detect volatility regime
            volatility_regime, atr_pct = self._detect_volatility_regime(nifty_ohlcv, vix_value)
            
            # Detect market regime
            market_regime = self._detect_market_regime(
                trend_type,
                nifty_ohlcv,
                bank_nifty_ohlcv if bank_nifty_ohlcv else nifty_ohlcv
            )
            
            # Calculate regime strength
            regime_strength = self._calculate_regime_strength(nifty_ohlcv, trend_type)
            
            regime_output = RegimeOutput(
                market_regime=market_regime,
                volatility_regime=volatility_regime,
                trend_type=trend_type,
                regime_strength=regime_strength,
                regime_probability=regime_strength,
                atr_percentile=atr_pct,
                vix_reading=vix_value,
                timestamp=datetime.now(),
                metadata={
                    'nifty_price': nifty_ohlcv[-1].close,
                    'nifty_change_pct': ((nifty_ohlcv[-1].close - nifty_ohlcv[-22].close) / nifty_ohlcv[-22].close * 100) if len(nifty_ohlcv) > 22 else 0,
                    'detected_at': datetime.now().isoformat()
                }
            )
            
            return regime_output
        
        except Exception as e:
            logger.error(f"Error detecting regime: {str(e)}")
            return self._create_default_regime()
    
    def _detect_trend(self, ohlcv: List) -> TrendType:
        """Detect trend direction and strength."""
        if len(ohlcv) < 20:
            return TrendType.RANGE
        
        closes = np.array([c.close for c in ohlcv[-50:]])
        
        # Calculate EMAs
        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50) if len(closes) > 50 else np.mean(closes)
        
        current_price = closes[-1]
        
        # Strong uptrend: Price > EMA20 > EMA50, and rising
        if current_price > ema_20 > ema_50:
            adx = self._calculate_adx(ohlcv[-50:])
            if adx > 35:
                return TrendType.STRONG_UPTREND
            else:
                return TrendType.UPTREND
        # Strong downtrend
        elif current_price < ema_20 < ema_50:
            adx = self._calculate_adx(ohlcv[-50:])
            if adx > 35:
                return TrendType.STRONG_DOWNTREND
            else:
                return TrendType.DOWNTREND
        else:
            return TrendType.RANGE
    
    def _detect_volatility_regime(
        self,
        ohlcv: List,
        vix_value: Optional[float] = None
    ) -> tuple:
        """Detect volatility regime and ATR percentile."""
        if len(ohlcv) < 30:
            return VolatilityRegimeType.NORMAL_VOLATILITY, 50.0
        
        # Calculate ATR
        atr_recent = self._calculate_atr(ohlcv[-20:])
        atr_historical = self._calculate_atr(ohlcv)
        
        # ATR percentile
        if atr_historical > 0:
            atr_pct = (atr_recent / atr_historical) * 100
        else:
            atr_pct = 50.0
        
        # Classify volatility
        if atr_pct < 60:
            volatility = VolatilityRegimeType.LOW_VOLATILITY
        elif atr_pct < 100:
            volatility = VolatilityRegimeType.NORMAL_VOLATILITY
        elif atr_pct < 150:
            volatility = VolatilityRegimeType.HIGH_VOLATILITY
        else:
            volatility = VolatilityRegimeType.EXTREME_VOLATILITY
        
        # Override with VIX if available
        if vix_value:
            if vix_value < 15:
                volatility = VolatilityRegimeType.LOW_VOLATILITY
            elif vix_value < 25:
                volatility = VolatilityRegimeType.NORMAL_VOLATILITY
            elif vix_value < 35:
                volatility = VolatilityRegimeType.HIGH_VOLATILITY
            else:
                volatility = VolatilityRegimeType.EXTREME_VOLATILITY
        
        return volatility, atr_pct
    
    def _detect_market_regime(
        self,
        trend: TrendType,
        nifty: List,
        bank_nifty: List
    ) -> MarketRegimeType:
        """Detect overall market regime."""
        # Calculate breadth (both indices participating)
        nifty_strength = self._calculate_trend_strength(nifty[-50:])
        bank_nifty_strength = self._calculate_trend_strength(bank_nifty[-50:]) if bank_nifty else nifty_strength
        
        breadth_confirmation = (nifty_strength + bank_nifty_strength) / 2
        
        if trend in [TrendType.STRONG_UPTREND, TrendType.UPTREND]:
            if breadth_confirmation > 0.7:
                return MarketRegimeType.STRONG_BULL
            else:
                return MarketRegimeType.WEAK_BULL
        elif trend in [TrendType.STRONG_DOWNTREND, TrendType.DOWNTREND]:
            if breadth_confirmation < -0.7:
                return MarketRegimeType.STRONG_BEAR
            else:
                return MarketRegimeType.WEAK_BEAR
        else:
            return MarketRegimeType.SIDEWAYS
    
    def _calculate_regime_strength(self, ohlcv: List, trend: TrendType) -> float:
        """Calculate how strong/confident the regime is (0-1)."""
        if len(ohlcv) < 10:
            return 0.5
        
        strength_val = self._calculate_trend_strength(ohlcv[-50:])
        
        # Normalize to 0-1
        strength = (strength_val + 1.0) / 2.0
        strength = max(0.0, min(1.0, strength))
        
        return strength
    
    def _calculate_trend_strength(self, ohlcv: List) -> float:
        """Calculate trend strength (-1 to +1, -1=strong down, +1=strong up)."""
        if len(ohlcv) < 2:
            return 0.0
        
        closes = np.array([c.close for c in ohlcv])
        
        # Count up and down days
        up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        down_days = len(closes) - up_days - 1
        
        total_days = up_days + down_days
        if total_days == 0:
            return 0.0
        
        trend_strength = (up_days - down_days) / total_days
        return trend_strength
    
    def _calculate_atr(self, ohlcv: List, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(ohlcv) < period:
            return 0.0
        
        tr_values = []
        for i in range(len(ohlcv)):
            if i == 0:
                tr = ohlcv[i].high - ohlcv[i].low
            else:
                tr = max(
                    ohlcv[i].high - ohlcv[i].low,
                    abs(ohlcv[i].high - ohlcv[i-1].close),
                    abs(ohlcv[i].low - ohlcv[i-1].close)
                )
            tr_values.append(tr)
        
        atr = np.mean(tr_values[-period:])
        return atr
    
    def _calculate_ema(self, values: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros(len(values))
        multiplier = 2 / (period + 1)
        
        ema[period-1] = np.mean(values[:period])
        
        for i in range(period, len(values)):
            ema[i] = (values[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def _calculate_adx(self, ohlcv: List, period: int = 14) -> float:
        """Calculate ADX (simplified)."""
        if len(ohlcv) < period:
            return 0.0
        
        up_moves = []
        down_moves = []
        
        for i in range(1, len(ohlcv)):
            high_diff = ohlcv[i].high - ohlcv[i-1].high
            low_diff = ohlcv[i-1].low - ohlcv[i].low
            
            if high_diff > 0 and high_diff > low_diff:
                up_moves.append(high_diff)
                down_moves.append(0)
            elif low_diff > 0 and low_diff > high_diff:
                up_moves.append(0)
                down_moves.append(low_diff)
            else:
                up_moves.append(0)
                down_moves.append(0)
        
        if len(up_moves) >= period:
            avg_up = np.mean(up_moves[-period:])
            avg_down = np.mean(down_moves[-period:])
            adx = abs(avg_up - avg_down) if (avg_up + avg_down) > 0 else 0
        else:
            adx = 0.0
        
        return adx
    
    def _create_default_regime(self) -> RegimeOutput:
        """Create default regime output."""
        return RegimeOutput(
            market_regime=MarketRegimeType.SIDEWAYS,
            volatility_regime=VolatilityRegimeType.NORMAL_VOLATILITY,
            trend_type=TrendType.RANGE,
            regime_strength=0.5,
            regime_probability=0.5,
            atr_percentile=50.0,
            timestamp=datetime.now()
        )
