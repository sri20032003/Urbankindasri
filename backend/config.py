"""
Global configuration and environment variables for Urbankinda.
Covers data providers, ML/RL models, risk management, monitoring, and feature flags.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / ".cache"

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# ============ DATABASE CONFIGURATION ============
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./urbankinda.db"
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# ============ REDIS CONFIGURATION ============
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

# ============ DATA PROVIDER CONFIGURATION ============
DATA_PROVIDER = os.getenv("DATA_PROVIDER", "yfinance")  # yfinance, zerodha, nse_api
NSE_API_KEY = os.getenv("NSE_API_KEY", None)
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", None)
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", None)

# ============ API CONFIGURATION ============
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_WORKERS = int(os.getenv("API_WORKERS", 4))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ============ FRONTEND CONFIGURATION ============
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 8080))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:3000").split(",")

# ============ ML MODEL CONFIGURATION ============
ML_MODELS_ENABLED = os.getenv("ML_MODELS_ENABLED", "true").lower() == "true"
RL_MODELS_ENABLED = os.getenv("RL_MODELS_ENABLED", "false").lower() == "true"
TRANSFORMER_ENABLED = os.getenv("TRANSFORMER_ENABLED", "false").lower() == "true"
AUTOML_ENABLED = os.getenv("AUTOML_ENABLED", "false").lower() == "true"

# Model retraining
MODEL_RETRAIN_FREQUENCY_HOURS = int(os.getenv("MODEL_RETRAIN_FREQUENCY_HOURS", 24))
MODEL_VALIDATION_SPLIT = float(os.getenv("MODEL_VALIDATION_SPLIT", 0.2))
MODEL_TEST_SPLIT = float(os.getenv("MODEL_TEST_SPLIT", 0.1))

# ============ SIGNAL CONFIGURATION ============
MIN_SIGNAL_QUALITY = int(os.getenv("MIN_SIGNAL_QUALITY", 70))
MIN_MODEL_AGREEMENT = float(os.getenv("MIN_MODEL_AGREEMENT", 0.6))
NO_TRADE_QUALITY_THRESHOLD = int(os.getenv("NO_TRADE_QUALITY_THRESHOLD", 65))

# Signal expiration
SIGNAL_VALIDITY_HOURS = int(os.getenv("SIGNAL_VALIDITY_HOURS", 4))
SIGNAL_REFRESH_INTERVAL_SECONDS = int(os.getenv("SIGNAL_REFRESH_INTERVAL_SECONDS", 60))

# ============ RISK MANAGEMENT CONFIGURATION ============
MAX_POSITION_SIZE_PCT = float(os.getenv("MAX_POSITION_SIZE_PCT", 5.0))
MAX_ACCOUNT_RISK_PCT = float(os.getenv("MAX_ACCOUNT_RISK_PCT", 2.0))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", 5.0))
MAX_DRAWDOWN_PCT = float(os.getenv("MAX_DRAWDOWN_PCT", 10.0))

# ============ VOLATILITY CONFIGURATION ============
VIX_LOW_THRESHOLD = float(os.getenv("VIX_LOW_THRESHOLD", 12))
VIX_NORMAL_THRESHOLD = float(os.getenv("VIX_NORMAL_THRESHOLD", 20))
VIX_HIGH_THRESHOLD = float(os.getenv("VIX_HIGH_THRESHOLD", 30))
VIX_EXTREME_THRESHOLD = float(os.getenv("VIX_EXTREME_THRESHOLD", 40))

# ============ LIQUIDITY CONFIGURATION ============
MIN_AVERAGE_VOLUME = int(os.getenv("MIN_AVERAGE_VOLUME", 100000))
MIN_AVERAGE_TURNOVER = float(os.getenv("MIN_AVERAGE_TURNOVER", 1000000))
MAX_ACCEPTABLE_SPREAD_BPS = int(os.getenv("MAX_ACCEPTABLE_SPREAD_BPS", 50))

# ============ MONITORING CONFIGURATION ============
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 8001))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============ NEWS & EVENTS CONFIGURATION ============
NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "newsapi")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", None)
SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")

# ============ BACKTEST CONFIGURATION ============
BACKTEST_START_DATE = os.getenv("BACKTEST_START_DATE", "2022-01-01")
BACKTEST_END_DATE = os.getenv("BACKTEST_END_DATE", "2024-12-31")
BACKTEST_COMMISSIONS = float(os.getenv("BACKTEST_COMMISSIONS", 0.0005))
BACKTEST_SLIPPAGE_BPS = float(os.getenv("BACKTEST_SLIPPAGE_BPS", 2.0))

# ============ HISTORICAL DATA CONFIGURATION ============
HISTORICAL_DATA_YEARS = int(os.getenv("HISTORICAL_DATA_YEARS", 3))
CACHE_HISTORICAL_DATA = os.getenv("CACHE_HISTORICAL_DATA", "true").lower() == "true"

# ============ NIFTY STOCKS CONFIGURATION ============
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFC", "WIPRO", "LT", "ASIANPAINT", "MARUTI",
    "SUNPHARMA", "BAJAJFINSV", "HDFCBANK", "ICICIBANK", "INDUSINDBK", "KOTAKBANK",
    "AXISBANK", "HINDUNILVR", "ITC", "BAJAJ-AUTO", "TATAMOTORS", "HCLTECH",
    "TECHM", "SBILIFE", "SBIN", "JSWSTEEL", "BAJAJHLDNG", "NTPC", "POWERGRID",
    "DRREDDY", "BHARTIARTL", "HDFCLIFE", "EICHERMOT", "ADANIPORTS", "ADANIGREEN",
    "GAIL", "ONGC", "COALINDIA", "IOC", "INDIGO", "BPCL", "M&M", "SIEMENS",
    "DIESITEC", "BOSCHLTD", "HEROMOTOCO", "BEL", "PAGEIND", "DMART"
]

WATCH_STOCKS = os.getenv("WATCH_STOCKS", ",".join(NIFTY_50_SYMBOLS)).split(",")

# ============ FEATURE FLAGS ============
ENABLE_MOCK_DATA = os.getenv("ENABLE_MOCK_DATA", "false").lower() == "true"
ENABLE_WALK_FORWARD = os.getenv("ENABLE_WALK_FORWARD", "true").lower() == "true"
ENABLE_OPTIONS_ENGINE = os.getenv("ENABLE_OPTIONS_ENGINE", "false").lower() == "true"
ENABLE_NEWS_ENGINE = os.getenv("ENABLE_NEWS_ENGINE", "true").lower() == "true"
ENABLE_SENTIMENT_ANALYSIS = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "true").lower() == "true"

# ============ SYSTEM CONFIGURATION ============
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))
TASK_QUEUE_MAX_SIZE = int(os.getenv("TASK_QUEUE_MAX_SIZE", 1000))
SYSTEM_HEALTH_CHECK_INTERVAL = int(os.getenv("SYSTEM_HEALTH_CHECK_INTERVAL", 60))

# ============ NOTIFICATION CONFIGURATION ============
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", None)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", None)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", None)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", None)
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", None)

# ============ VALIDATION RULES ============
assert MIN_SIGNAL_QUALITY >= 0 and MIN_SIGNAL_QUALITY <= 100, "MIN_SIGNAL_QUALITY must be 0-100"
assert MIN_MODEL_AGREEMENT >= 0 and MIN_MODEL_AGREEMENT <= 1, "MIN_MODEL_AGREEMENT must be 0-1"
assert MAX_POSITION_SIZE_PCT > 0, "MAX_POSITION_SIZE_PCT must be positive"
assert MAX_ACCOUNT_RISK_PCT > 0, "MAX_ACCOUNT_RISK_PCT must be positive"

# ============ DEBUG CONFIGURATION ============
if DEBUG:
    LOG_LEVEL = "DEBUG"
    DATABASE_ECHO = True
