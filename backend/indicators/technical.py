"""TechnicalIndicators - Comprehensive technical analysis"""
import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculates all technical indicators."""

    def __init__(self, config: Dict):
        self.config = config

    async def calculate_all(self, ohlcv: pd.DataFrame) -> Dict[str, any]:
        """Calculate all indicators."""
        try:
            indicators = {}

            # Momentum indicators
            indicators['rsi'] = self._rsi(ohlcv['close'])
            indicators['macd'] = self._macd(ohlcv['close'])
            indicators['stoch'] = self._stochastic(ohlcv)

            # Trend indicators
            indicators['adx'] = self._adx(ohlcv)
            indicators['ema12'] = ohlcv['close'].ewm(span=12).mean().iloc[-1]
            indicators['ema26'] = ohlcv['close'].ewm(span=26).mean().iloc[-1]
            indicators['sma50'] = ohlcv['close'].rolling(50).mean().iloc[-1]
            indicators['sma200'] = ohlcv['close'].rolling(200).mean().iloc[-1]

            # Volatility indicators
            indicators['atr'] = self._atr(ohlcv)
            indicators['bollinger'] = self._bollinger_bands(ohlcv['close'])

            # Volume indicators
            indicators['obv'] = self._obv(ohlcv)
            indicators['volume_sma'] = ohlcv['volume'].rolling(20).mean().iloc[-1]

            logger.debug(f"Calculated {len(indicators)} indicators")
            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}

    def _rsi(self, close: pd.Series, period: int = 14) -> float:
        """RSI calculation."""
        try:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss if loss.iloc[-1] != 0 else 0
            rsi = 100 - (100 / (1 + rs.iloc[-1]))
            return float(rsi)
        except:
            return 50.0

    def _macd(self, close: pd.Series) -> Dict[str, float]:
        """MACD calculation."""
        try:
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            return {
                'macd_line': float(macd_line.iloc[-1]),
                'signal_line': float(signal_line.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
        except:
            return {'macd_line': 0, 'signal_line': 0, 'histogram': 0}

    def _stochastic(self, ohlcv: pd.DataFrame, period: int = 14) -> Dict[str, float]:
        """Stochastic Oscillator."""
        try:
            low_min = ohlcv['low'].rolling(window=period).min()
            high_max = ohlcv['high'].rolling(window=period).max()
            k = ((ohlcv['close'] - low_min) / (high_max - low_min)) * 100
            d = k.rolling(window=3).mean()
            return {'k': float(k.iloc[-1]), 'd': float(d.iloc[-1])}
        except:
            return {'k': 50, 'd': 50}

    def _adx(self, ohlcv: pd.DataFrame, period: int = 14) -> float:
        """ADX (Average Directional Index)."""
        try:
            high = ohlcv['high']
            low = ohlcv['low']
            close = ohlcv['close']
            
            # Simplified ADX
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            
            # Directional Movement
            plus_dm = high.diff().where((high.diff() > 0) & (high.diff() > low.diff()*-1), 0)
            minus_dm = (low.diff() * -1).where((low.diff() * -1 > 0) & (low.diff() * -1 > high.diff()), 0)
            
            plus_di = (plus_dm.rolling(period).mean() / atr) * 100
            minus_di = (minus_dm.rolling(period).mean() / atr) * 100
            
            di_diff = abs(plus_di - minus_di)
            di_sum = plus_di + minus_di
            adx = (di_diff / di_sum * 100).rolling(period).mean()
            
            return float(adx.iloc[-1]) if adx.iloc[-1] > 0 else 25.0
        except:
            return 25.0

    def _atr(self, ohlcv: pd.DataFrame, period: int = 14) -> float:
        """ATR (Average True Range)."""
        try:
            high = ohlcv['high']
            low = ohlcv['low']
            close = ohlcv['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            
            return float(atr.iloc[-1])
        except:
            return 0.0

    def _bollinger_bands(self, close: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Bollinger Bands."""
        try:
            sma = close.rolling(period).mean()
            std = close.rolling(period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return {
                'upper': float(upper.iloc[-1]),
                'middle': float(sma.iloc[-1]),
                'lower': float(lower.iloc[-1])
            }
        except:
            return {'upper': 0, 'middle': 0, 'lower': 0}

    def _obv(self, ohlcv: pd.DataFrame) -> float:
        """On-Balance Volume."""
        try:
            close = ohlcv['close']
            volume = ohlcv['volume']
            
            obv = [0]
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.append(obv[-1] + volume.iloc[i])
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.append(obv[-1] - volume.iloc[i])
                else:
                    obv.append(obv[-1])
            
            return float(obv[-1])
        except:
            return 0.0
