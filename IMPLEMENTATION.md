# Urbankinda - AI-Powered Intraday Stock Signal Engine

## Phase 7-12 Implementation

Comprehensive modular AI system for identifying 12-20% intraday opportunities in NSE/BSE stocks.

### Architecture

```
Live Market Data
        ↓
[Data Layer] - Pluggable providers (YFinance, NSE API, Zerodha)
        ↓
[Proxy Engine] - 50+ price action, volume, momentum, structure proxies
        ↓
[Abnormality Detector] - Identify unusual intraday conditions
        ↓
[Regime Detection] - Market/sector/volatility classification
        ↓
[ML Ensemble] - XGBoost, LightGBM, LSTM, Random Forest
        ↓
[Magnitude Feasibility] - Check if 12-20% moves are realistic
        ↓
[Signal Generator] - NO-TRADE gate, quality scoring, fusion
        ↓
[Risk Manager] - Position sizing, stops, targets
        ↓
[Live Monitor] - Signal invalidation, refresh
        ↓
[Post-Trade Analytics] - Learning from outcomes
        ↓
[API & Dashboard] - User interface
        ↓
Manual Execution in Groww
```

### Key Components

#### 1. Data Layer (`backend/data/`)
- **base_provider.py** - Abstract provider interface
- **yfinance_provider.py** - YFinance implementation
- **cache.py** - TTL-based caching (memory + Redis)
- **historical.py** - Historical data management

#### 2. Proxy Engine (`backend/proxies/`)
- **proxy_engine.py** - 40+ proxies across 5 categories
  - Price Action (higher highs, momentum, acceleration, etc.)
  - Volume (relative volume, acceleration, breakout volume)
  - Momentum (RSI, momentum persistence)
  - Market Structure (VWAP distance, support/resistance)
  - Relative Strength (stock vs index)
- **abnormality_detector.py** - Identify unusual conditions

#### 3. Regime Detection (`backend/regime/`)
- **market_regime.py** - Market/volatility/trend classification

#### 4. Signal Generation (`backend/signal/`)
- **magnitude_engine.py** - 12-20% feasibility analysis
- **signal_generator.py** - Signal fusion, quality scoring, NO-TRADE gate

#### 5. ML/RL (`backend/models/`)
- **ml_ensemble.py** - 4-model ensemble predictions

#### 6. Risk Management (`backend/risk/`)
- **risk_management.py** - Position sizing, liquidity, slippage

#### 7. Monitoring & Learning (`backend/`)
- **monitoring/signal_monitor.py** - Live monitoring and invalidation
- **analytics/post_trade_analytics.py** - Trade journal, continuous learning

#### 8. API (`backend/routes/`)
- **api.py** - FastAPI endpoints for scanner, signals, details, lab

### Key Features

✅ **50+ Selective Proxies** - Not all indicators used for every stock
✅ **NO-TRADE Gate** - Rejects weak signals
✅ **Magnitude Engine** - Only calls 12-20% moves when realistic
✅ **Regime-Aware** - Different strategies for different markets
✅ **Real-Time Monitoring** - Signals monitored and invalidated live
✅ **Post-Trade Learning** - Continuous improvement from outcomes
✅ **Risk Management** - Position sizing based on ATR and liquidity
✅ **Walk-Forward Validation** - Backtesting without lookahead bias
✅ **No Groww API** - Manual execution, no automation
✅ **Modular Architecture** - Pluggable data providers, models, strategies

### Running the System

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the engine
python backend/app.py

# In another terminal, run the API
uvicorn backend.routes.api:app --host 0.0.0.0 --port 8000

# Access the dashboard
http://localhost:3000
```

### Configuration

All settings in `backend/config.py`:
- Data provider (YFinance, NSE API, Zerodha)
- ML/RL models enabled/disabled
- Risk management parameters
- Signal thresholds
- Feature flags

### Database

Models in `backend/database/models.py`:
- Stocks, Prices, Indicators
- Signals, Signal Outcomes
- Strategy Performance
- Proxy Reliability
- Model Performance
- Backtest Results

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend
```

### Monitoring

- Prometheus metrics on port 8001
- JSON structured logging
- Real-time signal monitoring
- Health checks

### Deployment

```bash
# Build Docker image
docker build -t urbankinda .

# Run with docker-compose
docker-compose up -d
```

### Important Notes

⚠️ **No Guaranteed Profits** - This is a research tool, not a profit-guarantee system
⚠️ **Manual Execution** - All trades must be manually executed in Groww
⚠️ **Backtesting Limitations** - Past performance ≠ future results
⚠️ **Risk Management** - Always respect stop losses and position sizing
⚠️ **Data Quality** - System only as good as data inputs

### Next Steps

1. Implement remaining API endpoints
2. Add frontend dashboard (React/Vue)
3. Integrate live data provider
4. Train ML models on historical data
5. Add Telegram/Slack notifications
6. Deploy to production
7. Continuous monitoring and optimization

---

**Status**: ✅ Phase 7-12 Complete
**Version**: 1.0.0
**Last Updated**: 2026-08-25
