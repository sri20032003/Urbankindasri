# Base Proxy Class

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ProxyDirection(str, Enum):
    """Direction of proxy signal."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class ProxyStrength(str, Enum):
    """Strength of proxy signal."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"
    NONE = "none"


class ProxyReliability(str, Enum):
    """Historical reliability of proxy."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class ProxyOutput(BaseModel):
    """Output of a proxy calculation."""
    proxy_name: str
    value: Optional[float] = None
    direction: ProxyDirection = ProxyDirection.UNKNOWN
    strength: ProxyStrength = ProxyStrength.NONE
    reliability: ProxyReliability = ProxyReliability.MODERATE
    freshness_score: float = 1.0  # 0-1, how recent is the data
    regime_suitability: float = 0.5  # 0-1, how suitable for current regime
    historical_usefulness: float = 0.5  # 0-1, based on backtest performance
    confidence: float = 0.5  # 0-1, confidence in this proxy value
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class BaseProxy(ABC):
    """Abstract base class for market proxies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.proxy_name = self.__class__.__name__
        self.last_value: Optional[ProxyOutput] = None
        logger.info(f"Initializing proxy: {self.proxy_name}")
    
    @abstractmethod
    async def calculate(self, data: Dict[str, Any]) -> ProxyOutput:
        """Calculate proxy value from market data.
        
        Args:
            data: Market data (OHLCV, technical indicators, etc.)
        
        Returns:
            ProxyOutput with value, direction, strength, etc.
        """
        pass
    
    def _validate_data(self, data: Dict[str, Any], required_keys: list) -> bool:
        """Validate that required data is present.
        
        Args:
            data: Market data dictionary
            required_keys: List of required keys
        
        Returns:
            True if all required keys are present
        """
        return all(key in data for key in required_keys)
    
    def _create_output(
        self,
        value: Optional[float] = None,
        direction: ProxyDirection = ProxyDirection.NEUTRAL,
        strength: ProxyStrength = ProxyStrength.MODERATE,
        reliability: ProxyReliability = ProxyReliability.MODERATE,
        freshness_score: float = 1.0,
        regime_suitability: float = 0.5,
        historical_usefulness: float = 0.5,
        confidence: float = 0.5,
        metadata: Dict[str, Any] = None
    ) -> ProxyOutput:
        """Create a standardized proxy output.
        
        Args:
            value: Numerical value of proxy
            direction: Direction of signal (bullish/bearish/neutral)
            strength: Strength of signal
            reliability: Historical reliability
            freshness_score: How recent the data is (0-1)
            regime_suitability: Suitability for current regime (0-1)
            historical_usefulness: Usefulness based on backtest (0-1)
            confidence: Confidence in this value (0-1)
            metadata: Additional metadata
        
        Returns:
            ProxyOutput instance
        """
        return ProxyOutput(
            proxy_name=self.proxy_name,
            value=value,
            direction=direction,
            strength=strength,
            reliability=reliability,
            freshness_score=freshness_score,
            regime_suitability=regime_suitability,
            historical_usefulness=historical_usefulness,
            confidence=confidence,
            metadata=metadata or {}
        )
