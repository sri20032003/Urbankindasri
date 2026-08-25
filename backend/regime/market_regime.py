"""
Market regime detection engine.
Classifies current market conditions into distinct regimes.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class RegimeOutput:
    """Market regime classification output."""
    timestamp: datetime
    market_regime: str  # STRONG_BULL, WEAK_BULL, SIDEWAYS, WEAK_BEAR, STRONG_BEAR
    volatility_regime: str  # LOW, NORMAL, HIGH, EXTREME
    trend_classification: str  # TREND, RANGE, BREAKOUT, BREAKDOWN, TRANSITION
    confidence: float  # 0-1
    nifty_momentum: float
    vix_level: float
    breadth: float  # advance/decline ratio

class RegimeDetectionEngine:
    """Detect market regime from NIFTY and VIX data."""
    
    def __init__(self):
        # VIX thresholds for volatility regime
        self.vix_low_threshold = 12
        self.vix_normal_threshold = 20
        self.vix_high_threshold = 30
        self.vix_extreme_threshold = 40
    
    def detect_regime(self, nifty_data: pd.DataFrame, vix_level: float, breadth: Dict) -> RegimeOutput:
        """
        Detect market regime from NIFTY and VIX data.
        
        Args:
            nifty_data: Historical NIFTY OHLCV data
            vix_level: Current India VIX level
            breadth: Market breadth metrics {advances, declines, new_highs, new_lows}
        
        Returns:
            RegimeOutput with detailed classification
        """
        timestamp = datetime.utcnow()
        
        # Calculate NIFTY momentum
        nifty_momentum = self._calculate_nifty_momentum(nifty_data)
        
        # Classify volatility regime
        volatility_regime = self._classify_volatility_regime(vix_level)
        
        # Classify market regime
        market_regime = self._classify_market_regime(nifty_momentum, vix_level, breadth)
        
        # Classify trend
        trend_classification = self._classify_trend(nifty_data)
        
        # Calculate confidence
        confidence = self._calculate_regime_confidence(nifty_data, vix_level)
        
        # Calculate breadth ratio
        breadth_ratio = breadth.get('advances', 0) / (breadth.get('advances', 1) + breadth.get('declines', 1))
        
        return RegimeOutput(
            timestamp=timestamp,
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            trend_classification=trend_classification,
            confidence=confidence,
            nifty_momentum=nifty_momentum,
            vix_level=vix_level,
            breadth=breadth_ratio
        )
    
    def _calculate_nifty_momentum(self, nifty_data: pd.DataFrame) -> float:
        """Calculate NIFTY momentum as percentage change."""
        if len(nifty_data) < 2:
            return 0.0
        
        current_close = nifty_data['close'].iloc[-1]
        previous_close = nifty_data['close'].iloc[-2]
        
        momentum_pct = (current_close - previous_close) / previous_close * 100
        return float(momentum_pct)
    
    def _classify_volatility_regime(self, vix_level: float) -> str:
        """Classify volatility regime based on VIX."""
        if vix_level < self.vix_low_threshold:
            return "LOW"
        elif vix_level < self.vix_normal_threshold:
            return "NORMAL"
        elif vix_level < self.vix_high_threshold:
            return "HIGH"
        else:
            return "EXTREME"
    
    def _classify_market_regime(self, nifty_momentum: float, vix_level: float, breadth: Dict) -> str:
        """Classify market regime based on multiple factors."""
        breadth_ratio = breadth.get('advances', 0) / (breadth.get('advances', 1) + breadth.get('declines', 1))
        
        if nifty_momentum > 0.5:
            if breadth_ratio > 0.65:
                return "STRONG_BULL"
            else:
                return "WEAK_BULL"
        elif nifty_momentum < -0.5:
            if breadth_ratio < 0.35:
                return "STRONG_BEAR"
            else:
                return "WEAK_BEAR"
        else:
            return "SIDEWAYS"
    
    def _classify_trend(self, nifty_data: pd.DataFrame) -> str:
        """Classify trend using EMA crossover."""
        if len(nifty_data) < 50:
            return "TRANSITION"
        
        # Simple EMA calculation
        ema_20 = nifty_data['close'].tail(20).mean()
        ema_50 = nifty_data['close'].tail(50).mean()
        
        current_price = nifty_data['close'].iloc[-1]
        
        if current_price > ema_20 > ema_50:
            return "TREND"  # Uptrend
        elif current_price < ema_20 < ema_50:
            return "TREND"  # Downtrend
        elif abs(current_price - ema_20) < (current_price * 0.02):
            return "BREAKOUT"  # Price breaking out of EMA
        else:
            return "RANGE"
    
    def _calculate_regime_confidence(self, nifty_data: pd.DataFrame, vix_level: float) -> float:
        """Calculate confidence in regime classification."""
        if len(nifty_data) < 20:
            return 0.5
        
        # Higher confidence if trend is clear
        recent_closes = nifty_data['close'].tail(20).values
        uptrend_count = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] > recent_closes[i-1])
        trend_clarity = uptrend_count / len(recent_closes)
        
        # Normalize trend clarity to 0-1
        trend_clarity = max(0, abs(trend_clarity - 0.5) * 2)  # 0 = mixed, 1 = clear trend
        
        # Lower confidence if VIX is extreme
        vix_confidence = 1.0 if vix_level < 40 else 0.7
        
        confidence = (trend_clarity + vix_confidence) / 2
        return float(confidence)

class SectorRegimeEngine:
    """Detect sector-level regime and momentum."""
    
    def __init__(self):
        self.sector_indices = {
            'IT': 'NIFTY_IT',
            'PHARMA': 'NIFTY_PHARMA',
            'BANK': 'NIFTY_BANK',
            'FINANCE': 'NIFTY_FINANCIAL_SERVICES',
            'AUTO': 'NIFTY_AUTO',
            'METAL': 'NIFTY_METALS',
            'REALTY': 'NIFTY_REALTY',
            'ENERGY': 'NIFTY_ENERGY',
            'PSU': 'NIFTY_PSU_BANK'
        }
    
    def detect_sector_regime(self, sector_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Detect regime for each sector.
        
        Args:
            sector_data: Dictionary mapping sector name to OHLCV data
        
        Returns:
            Dictionary with sector momentum scores
        """
        sector_momentum = {}
        
        for sector, data in sector_data.items():
            if len(data) < 2:
                sector_momentum[sector] = 0.0
                continue
            
            current_close = data['close'].iloc[-1]
            previous_close = data['close'].iloc[-2]
            momentum = (current_close - previous_close) / previous_close * 100
            
            sector_momentum[sector] = float(momentum)
        
        return sector_momentum
    
    def get_strongest_sector(self, sector_momentum: Dict[str, float]) -> str:
        """Get the strongest performing sector."""
        if not sector_momentum:
            return 'NEUTRAL'
        
        return max(sector_momentum, key=sector_momentum.get)
    
    def get_weakest_sector(self, sector_momentum: Dict[str, float]) -> str:
        """Get the weakest performing sector."""
        if not sector_momentum:
            return 'NEUTRAL'
        
        return min(sector_momentum, key=sector_momentum.get)
