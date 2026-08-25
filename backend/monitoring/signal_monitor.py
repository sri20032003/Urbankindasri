"""
Live signal monitoring and invalidation engine.
Continuously monitors signals and invalidates when conditions change.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class SignalInvalidation:
    """Signal invalidation event."""
    signal_id: int
    stock_symbol: str
    timestamp: datetime
    reason: str
    price_at_invalidation: float
    volume_at_invalidation: float

class LiveSignalMonitor:
    """Monitor and invalidate signals in real-time."""
    
    def __init__(self):
        self.monitored_signals = {}  # signal_id -> signal_data
        self.check_interval_seconds = 30  # Check every 30 seconds
    
    async def monitor_signal(self, signal_card, live_data_provider):
        """
        Continuously monitor a signal for invalidation.
        
        Args:
            signal_card: SignalCard object
            live_data_provider: Live data provider instance
        """
        signal_id = hash(signal_card.stock_symbol + str(signal_card.timestamp))
        self.monitored_signals[signal_id] = {
            'signal': signal_card,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        logger.info(f"Started monitoring signal {signal_id} for {signal_card.stock_symbol}")
        
        try:
            while signal_card.is_valid and datetime.utcnow() < signal_card.validity_until:
                await asyncio.sleep(self.check_interval_seconds)
                
                # Get live data
                current_price, volume, timestamp = live_data_provider.get_live_price(
                    signal_card.stock_symbol
                )
                
                if current_price is None:
                    logger.warning(f"No live data for {signal_card.stock_symbol}")
                    continue
                
                # Check invalidation conditions
                invalidation_reason = self._check_invalidation(
                    signal_card, current_price, volume
                )
                
                if invalidation_reason:
                    logger.info(f"Signal {signal_id} invalidated: {invalidation_reason}")
                    signal_card.is_valid = False
                    signal_card.invalidation_reason = invalidation_reason
                    self.monitored_signals[signal_id]['status'] = 'invalidated'
                    break
        
        finally:
            if signal_id in self.monitored_signals:
                del self.monitored_signals[signal_id]
    
    def _check_invalidation(self, signal_card, current_price: float, volume: float) -> Optional[str]:
        """
        Check if signal should be invalidated.
        
        Returns: Invalidation reason string or None if still valid
        """
        
        # Check if stop loss is hit
        if signal_card.action == 'BUY' and current_price <= signal_card.stop_loss:
            return f"Stop loss hit at {current_price}"
        
        if signal_card.action == 'SELL' and current_price >= signal_card.stop_loss:
            return f"Stop loss hit at {current_price}"
        
        # Check if target is hit
        if signal_card.action == 'BUY' and current_price >= signal_card.target_1:
            return f"Target 1 hit at {current_price}"
        
        if signal_card.action == 'SELL' and current_price <= signal_card.target_1:
            return f"Target 1 hit at {current_price}"
        
        # Check if volume has collapsed
        if volume < 100000:  # Arbitrary low threshold
            return "Volume collapse detected"
        
        # Check if time validity expired
        if datetime.utcnow() >= signal_card.validity_until:
            return "Signal validity expired"
        
        return None

class RealTimeSignalRefresh:
    """Refresh signals in real-time as conditions change."""
    
    def __init__(self, signal_generator, proxy_engine, market_regime_engine):
        self.signal_generator = signal_generator
        self.proxy_engine = proxy_engine
        self.market_regime_engine = market_regime_engine
        self.refresh_interval_seconds = 60
    
    async def continuous_refresh(self, watch_stocks: List[str], data_provider):
        """
        Continuously refresh signals for watched stocks.
        """
        logger.info(f"Starting continuous refresh for {len(watch_stocks)} stocks")
        
        while True:
            try:
                for symbol in watch_stocks:
                    try:
                        # Get current data
                        current_price, volume, timestamp = data_provider.get_live_price(symbol)
                        historical_data = data_provider.get_ohlcv(symbol, '5m', limit=100)
                        
                        if not current_price or not historical_data:
                            logger.warning(f"Insufficient data for {symbol}")
                            continue
                        
                        # Recalculate signal
                        # This would involve calling all the engines again
                        logger.debug(f"Refreshed signal for {symbol}")
                    
                    except Exception as e:
                        logger.error(f"Error refreshing {symbol}: {str(e)}")
                        continue
                
                await asyncio.sleep(self.refresh_interval_seconds)
            
            except Exception as e:
                logger.error(f"Error in continuous refresh: {str(e)}")
                await asyncio.sleep(self.refresh_interval_seconds)
