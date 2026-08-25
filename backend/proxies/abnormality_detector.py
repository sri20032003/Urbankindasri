"""
Abnormal move detection engine.
Identifies stocks experiencing unusual intraday conditions.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class AbnormalityScore:
    """Abnormality detection output."""
    symbol: str
    timestamp: datetime
    
    # Individual abnormality scores
    price_movement_score: float  # 0-100
    volume_abnormality_score: float  # 0-100
    volatility_expansion_score: float  # 0-100
    momentum_spike_score: float  # 0-100
    acceleration_score: float  # 0-100
    range_expansion_score: float  # 0-100
    
    # Overall
    overall_abnormality_score: float  # 0-100
    abnormality_type: str  # breakout, momentum_spike, volume_surge, volatility_shock, etc.
    rank_in_universe: int  # Position in sorted abnormality list

class AbnormalMoveDetector:
    """Detect stocks with abnormal intraday conditions."""
    
    def __init__(self):
        self.min_volume_threshold = 100000  # Minimum volume for consideration
    
    def detect_abnormalities(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> AbnormalityScore:
        """
        Detect abnormal conditions in a stock.
        
        Args:
            stock_data: Current OHLCV and metadata
            historical_baseline: Historical intraday data for comparison
        
        Returns:
            AbnormalityScore with detailed breakdown
        """
        symbol = stock_data['symbol']
        current_price = stock_data['current_price']
        current_volume = stock_data['current_volume']
        timestamp = stock_data['timestamp']
        
        # Check if volume meets minimum threshold
        if current_volume < self.min_volume_threshold:
            logger.warning(f"{symbol} volume below threshold: {current_volume}")
            return None
        
        # Calculate individual abnormality scores
        price_movement_score = self._calculate_price_abnormality(stock_data, historical_baseline)
        volume_abnormality_score = self._calculate_volume_abnormality(stock_data, historical_baseline)
        volatility_expansion_score = self._calculate_volatility_expansion(stock_data, historical_baseline)
        momentum_spike_score = self._calculate_momentum_spike(stock_data, historical_baseline)
        acceleration_score = self._calculate_acceleration(stock_data, historical_baseline)
        range_expansion_score = self._calculate_range_expansion(stock_data, historical_baseline)
        
        # Overall abnormality
        overall_score = np.mean([
            price_movement_score,
            volume_abnormality_score,
            volatility_expansion_score,
            momentum_spike_score,
            acceleration_score,
            range_expansion_score
        ])
        
        # Determine abnormality type
        abnormality_type = self._classify_abnormality_type({
            'price_movement': price_movement_score,
            'volume': volume_abnormality_score,
            'volatility': volatility_expansion_score,
            'momentum': momentum_spike_score,
            'acceleration': acceleration_score,
            'range': range_expansion_score
        })
        
        return AbnormalityScore(
            symbol=symbol,
            timestamp=timestamp,
            price_movement_score=price_movement_score,
            volume_abnormality_score=volume_abnormality_score,
            volatility_expansion_score=volatility_expansion_score,
            momentum_spike_score=momentum_spike_score,
            acceleration_score=acceleration_score,
            range_expansion_score=range_expansion_score,
            overall_abnormality_score=overall_score,
            abnormality_type=abnormality_type,
            rank_in_universe=0  # Will be set after sorting all stocks
        )
    
    def _calculate_price_abnormality(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Measure if price movement is abnormal vs historical."""
        if historical_baseline.empty:
            return 0.0
        
        current_move_pct = stock_data['intraday_change_pct']
        historical_avg_move = historical_baseline['intraday_range_pct'].mean()
        historical_std = historical_baseline['intraday_range_pct'].std()
        
        # Z-score of current move
        if historical_std == 0:
            z_score = 0
        else:
            z_score = abs(current_move_pct - historical_avg_move) / historical_std
        
        # Convert to 0-100 scale
        abnormality = min(z_score * 20, 100)
        return float(abnormality)
    
    def _calculate_volume_abnormality(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Measure if volume is abnormal."""
        if historical_baseline.empty:
            return 0.0
        
        current_volume = stock_data['current_volume']
        historical_avg_volume = historical_baseline['volume'].mean()
        historical_std = historical_baseline['volume'].std()
        
        # Z-score of current volume
        if historical_std == 0:
            z_score = 0
        else:
            z_score = abs(current_volume - historical_avg_volume) / historical_std
        
        # Convert to 0-100 scale
        abnormality = min(z_score * 15, 100)
        return float(abnormality)
    
    def _calculate_volatility_expansion(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Measure if volatility has expanded."""
        if historical_baseline.empty:
            return 0.0
        
        current_atr = stock_data.get('current_atr', 0)
        historical_avg_atr = historical_baseline['atr'].mean()
        
        if historical_avg_atr == 0:
            return 0.0
        
        expansion_ratio = current_atr / historical_avg_atr
        
        # Convert to 0-100 scale
        if expansion_ratio > 1.5:
            abnormality = min((expansion_ratio - 1) * 50, 100)
        else:
            abnormality = 0
        
        return float(abnormality)
    
    def _calculate_momentum_spike(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Detect if momentum has suddenly spiked."""
        if historical_baseline.empty:
            return 0.0
        
        current_momentum = stock_data.get('current_momentum', 0)
        historical_avg_momentum = historical_baseline['momentum'].mean()
        historical_std = historical_baseline['momentum'].std()
        
        if historical_std == 0:
            return 0.0
        
        z_score = abs(current_momentum - historical_avg_momentum) / historical_std
        abnormality = min(z_score * 25, 100)
        
        return float(abnormality)
    
    def _calculate_acceleration(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Measure if price/volume is accelerating."""
        current_acceleration = stock_data.get('price_acceleration', 0)
        
        # If acceleration exists, it's significant
        abnormality = min(abs(current_acceleration) * 100, 100)
        return float(abnormality)
    
    def _calculate_range_expansion(self, stock_data: Dict, historical_baseline: pd.DataFrame) -> float:
        """Measure if intraday range is expanding beyond normal."""
        if historical_baseline.empty:
            return 0.0
        
        current_range = stock_data.get('intraday_range_pct', 0)
        historical_avg_range = historical_baseline['intraday_range_pct'].mean()
        
        if historical_avg_range == 0:
            return 0.0
        
        expansion_ratio = current_range / historical_avg_range
        
        abnormality = max(0, (expansion_ratio - 1) * 50)
        abnormality = min(abnormality, 100)
        
        return float(abnormality)
    
    def _classify_abnormality_type(self, scores: Dict[str, float]) -> str:
        """Classify the type of abnormality detected."""
        max_score_type = max(scores, key=scores.get)
        
        type_map = {
            'price_movement': 'price_breakout',
            'volume': 'volume_surge',
            'volatility': 'volatility_shock',
            'momentum': 'momentum_spike',
            'acceleration': 'acceleration',
            'range': 'range_expansion'
        }
        
        return type_map.get(max_score_type, 'mixed_abnormality')
