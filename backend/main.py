# Main FastAPI Application

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.config import settings
from backend.data import DataManager
from backend.proxies import ProxyEngine
from backend.indicators import TechnicalIndicators, RegimeDetector
from backend.models import ModelManager
from backend.signal import SignalGenerator
from backend.api import signal_routes, stock_routes, dashboard_routes

logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown."""
    logger.info("Starting Urbankinda AI Signal Engine...")
    
    # Initialize managers
    app.data_manager = DataManager(settings.data_config)
    app.proxy_engine = ProxyEngine(settings.proxy_config)
    app.indicators = TechnicalIndicators(settings.indicator_config)
    app.regime_detector = RegimeDetector(settings.regime_config)
    app.model_manager = ModelManager(settings.model_config)
    app.signal_generator = SignalGenerator(settings.signal_config)
    
    # Start background update tasks
    app.update_task = asyncio.create_task(background_market_update(app))
    
    logger.info("✅ Urbankinda initialized successfully")
    yield
    
    # Cleanup
    logger.info("Shutting down Urbankinda...")
    if hasattr(app, 'update_task'):
        app.update_task.cancel()
    logger.info("✅ Urbankinda shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Urbankinda: AI Stock Signal Engine",
    description="Self-hosted AI-powered NSE/BSE stock analysis and signal generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Background tasks
async def background_market_update(app: FastAPI):
    """Continuous market data update and signal generation."""
    while True:
        try:
            await asyncio.sleep(settings.market_update_interval_seconds)
            
            # Fetch latest market data
            symbols = settings.watch_list
            
            for symbol in symbols:
                try:
                    # Get data
                    ohlcv = await app.data_manager.get_ohlcv(symbol)
                    if not ohlcv or len(ohlcv) < 50:
                        continue
                    
                    # Calculate indicators
                    indicators = await app.indicators.calculate_all(ohlcv)
                    
                    # Detect regime
                    regime = await app.regime_detector.detect_regime(ohlcv, indicators)
                    
                    # Generate signal (if applicable)
                    signal = await app.signal_generator.generate_signal(
                        symbol=symbol,
                        ohlcv=ohlcv,
                        indicators=indicators,
                        regime=regime
                    )
                    
                    if signal:
                        # Store signal in cache/database
                        await app.data_manager.store_signal(signal)
                
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Background update error: {str(e)}")


# Routes
app.include_router(signal_routes.router, prefix="/api/signals", tags=["Signals"])
app.include_router(stock_routes.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["Dashboard"])


# Health check
@app.get("/health")
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Urbankinda AI Signal Engine",
        "description": "Self-hosted AI-powered stock analysis for NSE/BSE",
        "api_docs": "/docs",
        "status": "running"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Run server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
