# Configuration & Environment Management

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Urbankinda"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./urbankinda.db"
    ECHO_SQL: bool = False
    
    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    USE_REDIS: bool = False
    
    # Data Providers
    NSE_DATA_PROVIDER: str = "yahoo"  # yahoo, zerodha, nse_direct
    BSE_DATA_PROVIDER: str = "yahoo"
    
    # API Keys
    YAHOO_FINANCE_API_KEY: Optional[str] = None
    ZERODHA_API_KEY: Optional[str] = None
    ZERODHA_ACCESS_TOKEN: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # ML/RL
    ML_MODEL_PATH: str = "models/ml_models/"
    RL_MODEL_PATH: str = "models/rl_models/"
    USE_GPU: bool = False
    MODEL_UPDATE_INTERVAL_HOURS: int = 24
    
    # Signal Configuration
    SIGNAL_REFRESH_INTERVAL_SECONDS: int = 60
    MIN_SIGNAL_QUALITY: int = 70
    MIN_CONFIDENCE: float = 0.60
    MAX_DAILY_SIGNALS: int = 50
    
    # Risk Management
    DEFAULT_ACCOUNT_RISK_PERCENT: float = 1.0
    MAX_DRAWDOWN_PERCENT: float = 10.0
    MAX_CORRELATION: float = 0.7
    
    # Data Quality
    MIN_DATA_QUALITY_SCORE: float = 0.8
    MAX_DATA_STALENESS_MINUTES: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/urbankinda.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Caching
    CACHE_TTL_SECONDS: int = 300
    CACHE_STRATEGY_TTL: int = 3600
    CACHE_BACKTEST_TTL: int = 86400
    
    # Backtesting
    WALK_FORWARD_WINDOW_DAYS: int = 90
    WALK_FORWARD_STEP_DAYS: int = 30
    MIN_TRADES_FOR_STRATEGY: int = 20
    MIN_ROBUSTNESS_SCORE: float = 0.65
    
    # Live Monitoring
    MONITOR_ACTIVE_SIGNALS: bool = True
    MONITOR_INTERVAL_SECONDS: int = 30
    MONITOR_MAX_WORKERS: int = 5
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    API_RATE_LIMIT: int = 1000
    
    # Feature Flags
    FEATURE_OPTIONS_ENGINE: bool = False
    FEATURE_CROSS_ASSET_ENGINE: bool = True
    FEATURE_FUNDAMENTAL_ENGINE: bool = True
    FEATURE_EVENT_DETECTION: bool = True
    FEATURE_NEWS_SENTIMENT: bool = True
    FEATURE_RL_ENSEMBLE: bool = True
    
    # Market Hours
    MARKET_OPEN_TIME: str = "09:15"
    MARKET_CLOSE_TIME: str = "15:30"
    MARKET_TIMEZONE: str = "Asia/Kolkata"
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Export singleton
settings = get_settings()
