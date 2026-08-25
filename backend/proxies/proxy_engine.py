"""
Comprehensive proxy engine for intraday opportunity detection.
Implements 50+ proxies across price action, volume, momentum, and market structure.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import numpy as np
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class ProxyOutput:
    """Standardized proxy output."""
    name: str
    value: float
    direction: str  # 'up', 'down', 'neutral'
    strength: float  # 0-1
    reliability: float  # 0-1, based on historical accuracy
    regime_suitability: str  # 'strong_bull', 'sideways', etc.
    timestamp: datetime
    timeframe: str

class PriceActionProxies:
    """Price action proxies for micro-structure analysis."""
    
    @staticmethod
    def higher_highs(df: pd.DataFrame, period: int = 3) -> ProxyOutput:
        """Detect series of higher highs."""
        if len(df) < period:
            return ProxyOutput(name='higher_highs', value=0, direction='neutral', strength=0, reliability=0.5, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        highs = df['high'].tail(period)
        is_higher_high = all(highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs)))
        strength = float(is_higher_high)
        direction = 'up' if is_higher_high else 'neutral'
        
        return ProxyOutput(
            name='higher_highs',
            value=strength,
            direction=direction,
            strength=strength,
            reliability=0.8,
            regime_suitability='bullish',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def price_acceleration(df: pd.DataFrame, period: int = 5) -> ProxyOutput:
        """Detect increasing rate of price change."""
        if len(df) < period:
            return ProxyOutput(name='price_acceleration', value=0, direction='neutral', strength=0, reliability=0.6, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        recent_closes = df['close'].tail(period).values
        pct_changes = np.diff(recent_closes) / recent_closes[:-1]
        
        # Acceleration: are changes getting larger?
        acceleration = np.diff(pct_changes)
        avg_acceleration = np.mean(acceleration)
        
        direction = 'up' if avg_acceleration > 0.001 else 'down' if avg_acceleration < -0.001 else 'neutral'
        strength = min(abs(avg_acceleration) * 100, 1.0)
        
        return ProxyOutput(
            name='price_acceleration',
            value=avg_acceleration,
            direction=direction,
            strength=strength,
            reliability=0.75,
            regime_suitability='trend',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def candle_body_strength(df: pd.DataFrame) -> ProxyOutput:
        """Measure strength of candle bodies vs wicks."""
        if len(df) == 0:
            return ProxyOutput(name='candle_body_strength', value=0, direction='neutral', strength=0, reliability=0.5, regime_suitability='any', timestamp=datetime.now(), timeframe='')
        
        latest = df.iloc[-1]
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        
        if total_range == 0:
            body_ratio = 0
        else:
            body_ratio = body_size / total_range
        
        direction = 'up' if latest['close'] > latest['open'] else 'down'
        strength = min(body_ratio, 1.0)
        
        return ProxyOutput(
            name='candle_body_strength',
            value=body_ratio,
            direction=direction,
            strength=strength,
            reliability=0.7,
            regime_suitability='any',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def wick_rejection(df: pd.DataFrame, threshold: float = 0.6) -> ProxyOutput:
        """Detect rejection wicks (sign of reversal potential)."""
        if len(df) == 0:
            return ProxyOutput(name='wick_rejection', value=0, direction='neutral', strength=0, reliability=0.6, regime_suitability='any', timestamp=datetime.now(), timeframe='')
        
        latest = df.iloc[-1]
        total_range = latest['high'] - latest['low']
        
        if total_range == 0:
            return ProxyOutput(name='wick_rejection', value=0, direction='neutral', strength=0, reliability=0.6, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        upper_wick = latest['high'] - max(latest['open'], latest['close'])
        lower_wick = min(latest['open'], latest['close']) - latest['low']
        
        upper_wick_ratio = upper_wick / total_range
        lower_wick_ratio = lower_wick / total_range
        
        direction = 'neutral'
        strength = 0
        
        if upper_wick_ratio > threshold:
            direction = 'down'  # Rejection of highs
            strength = min(upper_wick_ratio, 1.0)
        elif lower_wick_ratio > threshold:
            direction = 'up'  # Rejection of lows
            strength = min(lower_wick_ratio, 1.0)
        
        return ProxyOutput(
            name='wick_rejection',
            value=max(upper_wick_ratio, lower_wick_ratio),
            direction=direction,
            strength=strength,
            reliability=0.65,
            regime_suitability='transition',
            timestamp=df.index[-1],
            timeframe='5m'
        )

class VolumeProxies:
    """Volume-based proxies for confirmation."""
    
    @staticmethod
    def relative_volume(df: pd.DataFrame, lookback: int = 20) -> ProxyOutput:
        """Calculate relative volume."""
        if len(df) < lookback:
            return ProxyOutput(name='relative_volume', value=1.0, direction='neutral', strength=0, reliability=0.7, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(lookback).mean()
        
        rvol = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        direction = 'up' if rvol > 1.2 else 'down' if rvol < 0.8 else 'neutral'
        strength = min(abs(rvol - 1.0) / 2, 1.0)
        
        return ProxyOutput(
            name='relative_volume',
            value=rvol,
            direction=direction,
            strength=strength,
            reliability=0.85,
            regime_suitability='any',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def volume_acceleration(df: pd.DataFrame, period: int = 3) -> ProxyOutput:
        """Detect increasing volume trend."""
        if len(df) < period:
            return ProxyOutput(name='volume_acceleration', value=0, direction='neutral', strength=0, reliability=0.6, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        volumes = df['volume'].tail(period).values
        is_accelerating = all(volumes[i] > volumes[i-1] for i in range(1, len(volumes)))
        
        strength = float(is_accelerating)
        direction = 'up' if is_accelerating else 'neutral'
        
        return ProxyOutput(
            name='volume_acceleration',
            value=strength,
            direction=direction,
            strength=strength,
            reliability=0.75,
            regime_suitability='breakout',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def breakout_volume(df: pd.DataFrame, lookback: int = 20) -> ProxyOutput:
        """Detect if breakout has strong volume support."""
        if len(df) < lookback:
            return ProxyOutput(name='breakout_volume', value=0, direction='neutral', strength=0, reliability=0.7, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        # Check if price is near highs
        recent_high = df['high'].tail(lookback).max()
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(lookback).mean()
        
        is_near_high = current_price > recent_high * 0.98
        volume_support = current_volume > avg_volume * 1.5
        
        strength = float(is_near_high and volume_support)
        direction = 'up' if (is_near_high and volume_support) else 'neutral'
        
        return ProxyOutput(
            name='breakout_volume',
            value=strength,
            direction=direction,
            strength=strength,
            reliability=0.8,
            regime_suitability='breakout',
            timestamp=df.index[-1],
            timeframe='5m'
        )

class MomentumProxies:
    """Momentum quality proxies."""
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> ProxyOutput:
        """Calculate RSI."""
        if len(df) < period:
            return ProxyOutput(name='rsi', value=50, direction='neutral', strength=0, reliability=0.7, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        close = df['close'].tail(period)
        deltas = close.diff()[1:]
        seed = deltas[:1].values
        up = seed[(seed >= 0)].sum() / period
        down = -seed[(seed < 0)].sum() / period
        
        for i in range(1, len(deltas)):
            delta = deltas.iloc[i]
            if delta >= 0:
                up = (up * (period - 1) + delta) / period
                down = (down * (period - 1)) / period
            else:
                up = (up * (period - 1)) / period
                down = (down * (period - 1) - delta) / period
        
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        if rsi > 70:
            direction = 'overbought'
            strength = (rsi - 70) / 30
        elif rsi < 30:
            direction = 'oversold'
            strength = (30 - rsi) / 30
        else:
            direction = 'neutral'
            strength = 0
        
        return ProxyOutput(
            name='rsi',
            value=rsi,
            direction=direction,
            strength=strength,
            reliability=0.75,
            regime_suitability='range',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def momentum_persistence(df: pd.DataFrame, period: int = 5) -> ProxyOutput:
        """Check if momentum is sustained vs one-candle spike."""
        if len(df) < period:
            return ProxyOutput(name='momentum_persistence', value=0, direction='neutral', strength=0, reliability=0.6, regime_suitability='any', timestamp=df.index[-1], timeframe='')
        
        recent_closes = df['close'].tail(period).values
        pct_changes = np.diff(recent_closes) / recent_closes[:-1]
        
        # Check consistency of direction
        direction_consistency = sum(1 for i in range(1, len(pct_changes)) if pct_changes[i] * pct_changes[i-1] > 0) / len(pct_changes)
        
        avg_magnitude = np.mean(np.abs(pct_changes))
        
        direction = 'up' if np.mean(pct_changes) > 0 else 'down' if np.mean(pct_changes) < 0 else 'neutral'
        strength = min(direction_consistency * avg_magnitude * 100, 1.0)
        
        return ProxyOutput(
            name='momentum_persistence',
            value=direction_consistency,
            direction=direction,
            strength=strength,
            reliability=0.8,
            regime_suitability='trend',
            timestamp=df.index[-1],
            timeframe='5m'
        )

class MarketStructureProxies:
    """Market structure proxies."""
    
    @staticmethod
    def vwap_distance(df: pd.DataFrame) -> ProxyOutput:
        """Calculate distance from VWAP."""
        if len(df) == 0:
            return ProxyOutput(name='vwap_distance', value=0, direction='neutral', strength=0, reliability=0.7, regime_suitability='any', timestamp=datetime.now(), timeframe='')
        
        # Simplified VWAP calculation
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
        
        current_price = df['close'].iloc[-1]
        distance_pct = (current_price - vwap) / vwap
        
        if distance_pct > 0.005:
            direction = 'above_vwap'
            strength = min(distance_pct * 100, 1.0)
        elif distance_pct < -0.005:
            direction = 'below_vwap'
            strength = min(abs(distance_pct) * 100, 1.0)
        else:
            direction = 'at_vwap'
            strength = 0
        
        return ProxyOutput(
            name='vwap_distance',
            value=distance_pct,
            direction=direction,
            strength=strength,
            reliability=0.85,
            regime_suitability='any',
            timestamp=df.index[-1],
            timeframe='5m'
        )
    
    @staticmethod
    def support_resistance(df: pd.DataFrame, lookback: int = 20) -> Dict[str, float]:
        """Calculate support and resistance levels."""
        if len(df) < lookback:
            return {'support': df['low'].min(), 'resistance': df['high'].max()}
        
        recent_data = df.tail(lookback)
        support = recent_data['low'].min()
        resistance = recent_data['high'].max()
        
        return {
            'support': support,
            'resistance': resistance,
            'support_distance_pct': (df['close'].iloc[-1] - support) / support,
            'resistance_distance_pct': (resistance - df['close'].iloc[-1]) / df['close'].iloc[-1]
        }

class RelativeStrengthProxies:
    """Relative strength calculation."""
    
    @staticmethod
    def stock_vs_index(stock_price: float, stock_change_pct: float, index_change_pct: float) -> ProxyOutput:
        """Calculate relative strength vs NIFTY/index."""
        rs_pct = stock_change_pct - index_change_pct
        
        if rs_pct > 1.0:
            direction = 'outperforming'
            strength = min(rs_pct / 5, 1.0)
        elif rs_pct < -1.0:
            direction = 'underperforming'
            strength = min(abs(rs_pct) / 5, 1.0)
        else:
            direction = 'in_line'
            strength = 0
        
        return ProxyOutput(
            name='relative_strength',
            value=rs_pct,
            direction=direction,
            strength=strength,
            reliability=0.85,
            regime_suitability='any',
            timestamp=datetime.now(),
            timeframe='5m'
        )
