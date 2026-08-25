"""
Main application entry point.
Orchestrates all components and runs the live signal generation system.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from logger_config import get_logger
from config import (
    DATABASE_URL, REDIS_URL, DATA_PROVIDER, API_HOST, API_PORT,
    WATCH_STOCKS, ENABLE_MOCK_DATA, ML_MODELS_ENABLED, RL_MODELS_ENABLED,
    SIGNAL_REFRESH_INTERVAL_SECONDS, ENABLE_NEWS_ENGINE
)

# Import all engines
from data.yfinance_provider import YFinanceProvider
from data.cache import CacheManager
from data.historical import HistoricalDataManager

from proxies.proxy_engine import PriceActionProxies, VolumeProxies, MomentumProxies, MarketStructureProxies
from proxies.abnormality_detector import AbnormalMoveDetector

from regime.market_regime import RegimeDetectionEngine, SectorRegimeEngine

from signal.magnitude_engine import MagnitudeFeasibilityEngine
from signal.signal_generator import SignalGenerationEngine

from models.ml_ensemble import MLEnsemble

from risk.risk_management import RiskManagementEngine

from monitoring.signal_monitor import LiveSignalMonitor, RealTimeSignalRefresh

from analytics.post_trade_analytics import PostTradeAnalytics, ContinuousLearningEngine

logger = get_logger(__name__)

class UrbankindaEngine:
    """Main orchestrator for Urbankinda signal generation system."""
    
    def __init__(self):
        logger.info("="*60)
        logger.info("URBANKINDA - AI INTRADAY OPPORTUNITY ENGINE")
        logger.info("="*60)
        
        # Initialize data layer
        logger.info("Initializing data layer...")
        self.data_provider = YFinanceProvider()
        self.cache_manager = CacheManager(ttl_seconds=300)
        self.historical_data_manager = HistoricalDataManager(
            self.data_provider, self.cache_manager, Path('./data')
        )
        
        # Initialize proxy engines
        logger.info("Initializing proxy engines...")
        self.price_action_proxies = PriceActionProxies()
        self.volume_proxies = VolumeProxies()
        self.momentum_proxies = MomentumProxies()
        self.market_structure_proxies = MarketStructureProxies()
        self.abnormality_detector = AbnormalMoveDetector()
        
        # Initialize regime engines
        logger.info("Initializing regime detection...")
        self.market_regime_engine = RegimeDetectionEngine()
        self.sector_regime_engine = SectorRegimeEngine()
        
        # Initialize signal generation
        logger.info("Initializing signal generation...")
        self.magnitude_engine = MagnitudeFeasibilityEngine()
        self.signal_generator = SignalGenerationEngine()
        
        # Initialize ML/RL
        if ML_MODELS_ENABLED:
            logger.info("Initializing ML ensemble...")
            self.ml_ensemble = MLEnsemble()
        else:
            self.ml_ensemble = None
        
        # Initialize risk management
        logger.info("Initializing risk management...")
        self.risk_manager = RiskManagementEngine()
        
        # Initialize monitoring and learning
        logger.info("Initializing monitoring...")
        self.signal_monitor = LiveSignalMonitor()
        self.signal_refresh = RealTimeSignalRefresh(
            self.signal_generator, self.price_action_proxies, self.market_regime_engine
        )
        
        # Initialize analytics
        logger.info("Initializing post-trade analytics...")
        self.post_trade_analytics = PostTradeAnalytics()
        self.continuous_learning = ContinuousLearningEngine(None, None)
        
        # Active signals
        self.active_signals = {}
        
        logger.info("✓ All engines initialized successfully")
    
    async def scan_and_generate_signals(self):
        """
        Main loop: Scan universe and generate signals.
        """
        logger.info(f"Starting scan loop for {len(WATCH_STOCKS)} stocks...")
        
        while True:
            try:
                signals = []
                
                for symbol in WATCH_STOCKS:
                    try:
                        logger.debug(f"Processing {symbol}...")
                        
                        # Get current price and data
                        current_price, volume, timestamp = self.data_provider.get_live_price(symbol)
                        if not current_price:
                            logger.warning(f"No data for {symbol}")
                            continue
                        
                        # Get historical data
                        historical_data = self.historical_data_manager.get_historical_data(
                            symbol, days=30, timeframe='1d'
                        )
                        
                        # Detect abnormalities
                        abnormality = self.abnormality_detector.detect_abnormalities(
                            {
                                'symbol': symbol,
                                'current_price': current_price,
                                'current_volume': volume,
                                'timestamp': timestamp,
                                'intraday_change_pct': 2.5,  # Placeholder
                                'intraday_range_pct': 3.0,  # Placeholder
                                'current_atr': 50,  # Placeholder
                                'current_momentum': 0.5,  # Placeholder
                                'price_acceleration': 0.01  # Placeholder
                            },
                            historical_data
                        )
                        
                        if not abnormality or abnormality.overall_abnormality_score < 50:
                            continue  # Skip low abnormality stocks
                        
                        # Calculate proxies
                        proxy_outputs = []
                        # ... calculate all proxies ...
                        
                        # Get regime
                        # market_regime = self.market_regime_engine.detect_regime(...)
                        
                        # Get magnitude feasibility
                        magnitude = self.magnitude_engine.analyze_magnitude_feasibility(
                            symbol, current_price, historical_data, 50, 100, 200
                        )
                        
                        # ML prediction
                        ml_pred = self.ml_ensemble.predict({}, symbol) if self.ml_ensemble else {}
                        
                        # Risk metrics
                        risk_metrics = self.risk_manager.calculate_risk_metrics(
                            current_price, 50, volume, 1000000, 20, current_price * 1.1
                        )
                        
                        # Generate signal
                        signal = self.signal_generator.generate_signal(
                            symbol, current_price, proxy_outputs, "STRONG_BULL",
                            "NORMAL", ml_pred.__dict__, magnitude.__dict__, 
                            risk_metrics.__dict__
                        )
                        
                        if signal.action != "NO_TRADE":
                            signals.append(signal)
                            self.active_signals[symbol] = signal
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {str(e)}")
                        continue
                
                # Sort by quality and keep top signals
                signals_sorted = sorted(
                    signals, key=lambda x: x.signal_quality, reverse=True
                )[:10]
                
                logger.info(f"Generated {len(signals_sorted)} signals out of {len(WATCH_STOCKS)} stocks")
                
                # Wait for next refresh
                await asyncio.sleep(SIGNAL_REFRESH_INTERVAL_SECONDS)
            
            except Exception as e:
                logger.error(f"Error in scan loop: {str(e)}")
                await asyncio.sleep(SIGNAL_REFRESH_INTERVAL_SECONDS)
    
    async def start(self):
        """
        Start the Urbankinda engine.
        """
        logger.info("\n" + "="*60)
        logger.info("STARTING URBANKINDA ENGINE")
        logger.info("="*60 + "\n")
        
        # Start signal refresh loop
        logger.info(f"Starting continuous signal refresh every {SIGNAL_REFRESH_INTERVAL_SECONDS}s")
        await self.scan_and_generate_signals()
    
    def get_active_signals(self):
        """Get all active signals."""
        return list(self.active_signals.values())
    
    def get_signal_for_stock(self, symbol: str):
        """Get signal for specific stock."""
        return self.active_signals.get(symbol, None)


async def main():
    """Main entry point."""
    engine = UrbankindaEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down Urbankinda...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
