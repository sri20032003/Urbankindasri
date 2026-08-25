# Urbankinda: AI-Powered NSE/BSE Stock Signal Generator

**Self-hosted AI research and signal-generation system for Indian equities**

## Overview

Urbankinda is a sophisticated, modular AI system designed to:

- **Analyze** stocks continuously using live/near-live market data
- **Generate** selective BUY/SELL/HOLD/WAIT/NO-TRADE signals
- **Dynamically select** indicator combinations and proxies based on stock behavior and market regime
- **Estimate** entry zones, stop-loss, targets, risk/reward, and confidence
- **Work independently** without requiring Groww API integration
- **Present signals** for manual execution by the user in Groww

## Core Philosophy

This is **NOT** a system where:
```
RSI > 50 + MACD bullish = BUY
```

Instead, it implements:
```
STOCK → BEHAVIOR → REGIME → LIVE PROXIES → SELECTIVE COMBINATION
→ ML ENSEMBLE → RL ENSEMBLE → NEWS/EVENTS → CONFIRMATION
→ UNCERTAINTY → TARGET SPACE → EXPECTED VALUE → RISK → SIGNAL QUALITY
```

## Key Features

### 1. **Live Proxy Engine** (50+ Observable Proxies)
- Price-action proxies (breakouts, structure, compression)
- Market-structure proxies (support, resistance, levels)
- Technical indicators (RSI, MACD, ADX, EMA, VWAP, Bollinger Bands, etc.)
- Volume proxies (relative volume, accumulation/distribution, OBV, MFI)
- Momentum quality engine
- Relative strength vs NIFTY/sector

### 2. **Selective Indicator Combination Discovery**
- Candidate combinations: EMA+ADX+VWAP+Volume, RSI+VWAP+Bollinger, Breakout+RS+Volume, etc.
- Historical performance metrics for each combination
- Walk-forward validation (train → validate → test → move window)
- Overfitting protection

### 3. **Stock Characterization Engine**
- Behavioral profile: beta, liquidity, volatility, trend tendency, mean-reversion tendency, momentum tendency
- Regime-specific strategy selection
- Continuous profile updates

### 4. **Regime Detection**
- Market regime: STRONG BULL / WEAK BULL / SIDEWAYS / WEAK BEAR / STRONG BEAR
- Volatility regime: LOW / NORMAL / HIGH / EXTREME
- Trend detection: TREND / RANGE / BREAKOUT / BREAKDOWN / TRANSITION

### 5. **ML Ensemble**
- XGBoost, LightGBM, Random Forest, LSTM, Transformer models
- Predicts: direction probability, expected return, volatility, target probability, stop probability
- Model agreement scoring

### 6. **RL Ensemble**
- PPO, SAC agents optimizing for risk-adjusted returns
- Accounts for: transaction costs, slippage, liquidity, drawdown

### 7. **Market Intelligence**
- Sector rotation engine (sector momentum, breadth, relative strength)
- Market breadth (advance/decline, new highs/lows)
- Volatility engine (ATR, India VIX, volatility regime)
- News & sentiment processing
- Event-risk detection (earnings, dividends, corporate actions)

### 8. **Target-Space Analysis**
- Determines feasibility of 2×, 3×, 5× scenarios
- Never forces unrealistic targets
- Historical move distribution analysis

### 9. **Risk Management**
- Entry optimizer (breakout, pullback, retest, VWAP, support)
- Stop-loss optimizer (ATR-based, structure-based, volatility-adjusted)
- Position-sizing engine (account risk, confidence, liquidity, correlation)
- Risk/reward calculation

### 10. **Signal Quality Scoring**
- Combines: technical, volume, momentum, relative strength, sector confirmation, ML, RL, news, uncertainty
- Output: 0–100 signal quality score
- **NO-TRADE gate**: Rejects weak or forced signals

### 11. **Live Monitoring & Signal Expiration**
- Continuous monitoring of price, volume, momentum, VWAP, sector, market
- Automatic signal invalidation on regime/thesis changes
- Signal validity period with timestamp

### 12. **Post-Trade Learning**
- Records: stock, timestamp, regime, proxies, ML/RL output, entry/stop/targets, actual outcome (MFE/MAE)
- Continuous strategy ranking by robustness
- Improvement of proxy selection and combinations

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Dashboard)                 │
│  Scanner | Stock Detail | Signal Cards | Strategy Lab   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API / Application Layer                    │
│  Signal Generation | Risk Management | Live Monitoring  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Data Ingestion Layer (Pluggable)              │
│  NSE/BSE API | Yahoo Finance | Zerodha | Alternative   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Feature / Proxy Engine                        │
│  Price Action | Volume | Technical | Momentum | RS     │
└────────────────────┬────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼──┐  ┌────────▼─────────┐  ┌──▼────┐
│ ML   │  │ Regime Detection │  │  RL   │
│Engine│  │ & Market Intel   │  │Engine │
└──────┘  └──────────────────┘  └───────┘
    │                │                │
    └────────────────┼────────────────┘
                     │
         ┌───────────▼────────────┐
         │  Signal Fusion Engine  │
         │  - Quality Scoring     │
         │  - Risk/Reward Calc    │
         │  - NO-TRADE Gate       │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │   Signal Output        │
         │  - Signal Card         │
         │  - Explanation         │
         │  - Validity Period     │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │   Database & Cache     │
         │  - Stock Data          │
         │  - Indicators          │
         │  - Signals             │
         │  - Performance         │
         └────────────────────────┘
```

## Project Structure

```
Urbankinda/
├── backend/
│   ├── app.py                          # Main FastAPI app
│   ├── requirements.txt                # Python dependencies
│   ├── config.py                       # Configuration & environment variables
│   ├── logger_config.py                # Logging setup
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── base_provider.py            # Abstract base for data providers
│   │   ├── nse_provider.py             # NSE data ingestion
│   │   ├── bse_provider.py             # BSE data ingestion
│   │   ├── cache.py                    # Caching layer
│   │   └── historical.py               # Historical data management
│   │
│   ├── proxies/
│   │   ├── __init__.py
│   │   ├── base_proxy.py               # Abstract proxy class
│   │   ├── price_action.py             # Price-action proxies
│   │   ├── market_structure.py         # Support, resistance, levels
│   │   ├── technical_indicators.py     # RSI, MACD, ADX, EMA, etc.
│   │   ├── volume_proxies.py           # Volume, OBV, MFI, RVOL
│   │   ├── momentum_engine.py          # Momentum quality metrics
│   │   ├── relative_strength.py        # Stock vs NIFTY/sector
│   │   └── options_proxies.py          # Options data (where available)
│   │
│   ├── regime/
│   │   ├── __init__.py
│   │   ├── market_regime.py            # Market regime detection
│   │   ├── volatility_regime.py        # Volatility classification
│   │   ├── trend_detection.py          # Trend vs range vs breakout
│   │   ├── sector_analysis.py          # Sector rotation & breadth
│   │   └── breadth_engine.py           # Market-wide breadth metrics
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ml_ensemble.py              # XGBoost, LightGBM, RF, LSTM
│   │   ├── rl_ensemble.py              # PPO, SAC agents
│   │   ├── prediction_output.py        # Unified output format
│   │   └── model_manager.py            # Model lifecycle
│   │
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── combination_discovery.py    # Find best indicator combos
│   │   ├── walk_forward.py             # Walk-forward validation
│   │   ├── backtest.py                 # Historical testing
│   │   ├── overfitting_detector.py     # Overfitting checks
│   │   └── performance_tracker.py      # Strategy ranking
│   │
│   ├── signal/
│   │   ├── __init__.py
│   │   ├── entry_optimizer.py          # Entry point selection
│   │   ├── stop_loss_optimizer.py      # Stop-loss placement
│   │   ├── target_optimizer.py         # Target selection
│   │   ├── target_space.py             # 2×/3×/5× feasibility
│   │   ├── risk_reward.py              # R:R calculation
│   │   ├── quality_scorer.py           # Signal quality 0–100
│   │   ├── signal_generator.py         # Main signal generation
│   │   └── signal_expiration.py        # Validity period management
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── position_sizing.py          # Position size calculation
│   │   ├── liquidity_analyzer.py       # Spread, slippage, execution
│   │   ├── drawdown_manager.py         # Drawdown tracking
│   │   └── uncertainty_engine.py       # Confidence & uncertainty
│   │
│   ├── news/
│   │   ├── __init__.py
│   │   ├── news_provider.py            # News data ingestion
│   │   ├── sentiment_analyzer.py       # Sentiment scoring
│   │   ├── event_detector.py           # Earnings, dividends, corporate actions
│   │   └── fundamental_context.py      # Revenue, earnings, margins
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── live_monitor.py             # Real-time monitoring
│   │   ├── signal_updater.py           # Signal refresh & invalidation
│   │   └── health_check.py             # System health monitoring
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                       # SQLAlchemy setup
│   │   ├── models.py                   # ORM models
│   │   └── crud.py                     # Database operations
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── scanner.py                  # Stock scanner endpoint
│   │   ├── signal.py                   # Signal generation & details
│   │   ├── stock.py                    # Stock detail page
│   │   ├── strategy.py                 # Strategy lab
│   │   ├── proxy.py                    # Proxy lab
│   │   ├── performance.py              # Model performance tracking
│   │   └── backtest.py                 # Backtest & walk-forward
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── signal_refresh.py           # Background signal refresh
│   │   ├── data_sync.py                # Background data ingestion
│   │   └── model_retraining.py         # Periodic model updates
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py               # Input validation
│       ├── helpers.py                  # Utility functions
│       └── error_handlers.py           # Error handling
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js                      # Main app logic
│   │   ├── scanner.js                  # Scanner view
│   │   ├── signal_card.js              # Signal rendering
│   │   ├── stock_detail.js             # Stock detail view
│   │   ├── strategy_lab.js             # Strategy lab
│   │   ├── proxy_lab.js                # Proxy lab
│   │   ├── chart.js                    # Chart rendering
│   │   └── api_client.js               # API communication
│   │
│   └── components/
│       ├── scanner.html
│       ├── signal_card.html
│       ├── stock_detail.html
│       ├── strategy_lab.html
│       ├── proxy_lab.html
│       ├── backtest_lab.html
│       └── trade_journal.html
│
├── tests/
│   ├── unit/
│   │   ├── test_proxies.py
│   │   ├── test_regime.py
│   │   ├── test_ml_models.py
│   │   └── test_signal_generation.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_data_flow.py
│   └── backtest/
│       └── test_walk_forward.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROXY_REFERENCE.md
│   ├── SIGNAL_GENERATION.md
│   ├── API_DOCS.md
│   └── DEPLOYMENT.md
│
├── .env.example
├── .env.local (gitignored)
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── LICENSE
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL or SQLite
- Redis (optional, for caching)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ravichandranash234-png/Urbankinda.git
cd Urbankinda

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Run database migrations (if applicable)
# python -m alembic upgrade head

# Start the backend
python app.py

# In another terminal, start the frontend
cd ../frontend
python -m http.server 8080
```

### Using Docker

```bash
docker-compose up -d
```

## Signal Output Example

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    AI TRADE SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOCK:                          RELIANCE

ACTION:                         🟢 BUY

REGIME:                         Strong Bull / Normal Volatility

SELECTED SETUP:
  Breakout + RVOL + Relative Strength + VWAP + Market Confirmation

SIGNAL QUALITY:                 91 / 100
CONFIDENCE:                     84%
UNCERTAINTY:                    LOW

ENTRY ZONE:                     ₹2845 – ₹2855
STOP LOSS:                      ₹2820

TARGET 1:                       ₹2920 (R:R = 1:2.1)
TARGET 2:                       ₹2970 (R:R = 1:2.8)

TARGET SCENARIO:                2×–3× scenario feasible

MODEL AGREEMENT:                8 / 10

SIGNAL VALID UNTIL:             2026-08-25 15:30:00 IST

TOP 5 SUPPORTING PROXIES:
  1. Relative Strength:         STRONG (Stock outperforming sector)
  2. Breakout Volume:           STRONG (3.2× average volume)
  3. Sector Confirmation:       POSITIVE (IT sector bullish)
  4. ML Probability:            86% (XGBoost + LSTM consensus)
  5. Regime:                    FAVOURABLE (NIFTY in uptrend)

TOP 3 RISKS:
  1. Resistance:                ₹2970 (previous swing high)
  2. Volatility:                Slightly elevated (VIX at 65th percentile)
  3. Market Breadth:            Weakening (new lows increasing)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  IMPORTANT: Manual execution required in Groww
    This is a research signal, not a guaranteed profit.
    Position sizing and risk management are YOUR responsibility.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Signal Interpretation

### Actions
- **BUY**: Strong bullish confluence, positive risk/reward, quality ≥ 75
- **SELL**: Strong bearish confluence, quality ≥ 75
- **HOLD**: Existing position in favorable structure
- **WAIT**: Setup forming, wait for confirmation
- **NO TRADE**: Insufficient evidence, poor risk/reward, or excessive uncertainty

### Confidence Levels
- **HIGH**: 80%+ agreement across models, clear structure, strong volume
- **MEDIUM**: 60–80% agreement, mixed signals, acceptable uncertainty
- **LOW**: <60% agreement, high disagreement, avoid signal

### Uncertainty Classification
- **LOW**: Strong model agreement, clear regime, quality > 85
- **MEDIUM**: Moderate disagreement, regime transition, quality 70–85
- **HIGH**: Poor model agreement, conflicting signals, quality < 70

## Live Monitoring

Once a signal is generated, the system continuously monitors:

- **Price**: If stop is hit or target reached
- **Volume**: If volume dries up, signal may invalidate
- **Momentum**: If momentum reverses sharply
- **Regime**: If market regime changes
- **Sector**: If sector momentum reverses
- **News**: If significant news breaks
- **Relative Strength**: If relative strength reverses
- **Target Probability**: If target becomes unreachable

If any critical condition fails → **SIGNAL INVALID** (automatic recalculation)

## Dashboard Modes

### 1. **Live Scanner**
Real-time watchlist of all stocks with active signals.

### 2. **Stock Detail**
Deep dive: price chart, volume, indicators, regime, sector, relative strength, news, options context, ML/RL output, historical analogues, target scenarios, risk/reward.

### 3. **Signal History**
All generated signals with outcomes: entry, stop, target, MFE, MAE, P&L.

### 4. **Strategy Lab**
Which indicator combinations work? Which combinations are currently active? Which recently deteriorated?

### 5. **Proxy Lab**
Inspect all 50+ proxies: current value, direction, strength, reliability, historical usefulness.

### 6. **Backtest Lab**
Test indicator combinations on historical data. Walk-forward validation. Out-of-sample testing.

### 7. **Regime Lab**
Analyze current market regime. Historical regime performance. Strategy ranking by regime.

### 8. **Model Performance**
Accuracy, precision, recall, calibration. Expected return, drawdown. Regime-specific performance.

### 9. **Trade Journal**
All signals, outcomes, MFE/MAE, slippage, holding time, P&L.

### 10. **Risk Dashboard**
Position exposure, correlation, drawdown, VaR, expected loss.

## API Endpoints

### Scanner
- `GET /api/scanner` – Live stock scanner with active signals
- `GET /api/scanner?regime=strong_bull` – Filter by regime
- `GET /api/scanner?min_quality=75` – Filter by quality threshold

### Signals
- `GET /api/signals/active` – All active signals
- `GET /api/signals/{symbol}` – Signal for a specific stock
- `POST /api/signals/{symbol}/refresh` – Force signal recalculation
- `GET /api/signals/history?stock=RELIANCE` – Signal history

### Stock Details
- `GET /api/stock/{symbol}` – Full stock profile
- `GET /api/stock/{symbol}/proxies` – All proxy values for a stock
- `GET /api/stock/{symbol}/regime` – Current regime classification
- `GET /api/stock/{symbol}/chart?timeframe=1d&bars=100` – Historical data

### Strategies
- `GET /api/strategy/combinations` – All indicator combinations
- `GET /api/strategy/combinations?stock=RELIANCE` – Combinations for a stock
- `GET /api/strategy/combinations?regime=strong_bull` – Combinations for regime
- `GET /api/strategy/performance?combo=ema_adx_vwap` – Performance metrics

### Backtesting
- `POST /api/backtest` – Run walk-forward backtest
- `GET /api/backtest/results/{test_id}` – Backtest results

## No-Trade Gate Logic

Before generating a signal, the system checks:

```python
if not (data_reliable and
        liquidity_sufficient and
        market_regime_suitable and
        entry_location_good and
        target_space_sufficient and
        expected_value_positive and
        risk_acceptable and
        uncertainty_acceptable and
        not excessive_event_risk and
        not models_conflicting):
    return NO_TRADE
```

This ensures that **NO TRADE is preferred over a weak or forced signal**.

## Post-Trade Learning

Every signal is recorded with:
- **Intended**: Entry, stop, target, expected R:R
- **Actual**: Entry price, exit price, holding time, actual R:R, MFE, MAE
- **Analysis**: Was the setup valid? Which proxies were useful? Which failed?

This data feeds into:
- Proxy usefulness ranking
- Indicator combination robustness scores
- Regime-specific strategy selection
- Model performance tracking
- Continuous system improvement

## Important Disclaimers

⚠️ **This system does NOT:**
- Guarantee profits
- Guarantee zero losses
- Eliminate market risk
- Provide financial advice
- Automatically execute trades
- Replace human judgment

✅ **This system DOES:**
- Provide research and analysis
- Generate selective, high-quality signals
- Explain the reasoning behind signals
- Help manage risk
- Support decision-making

## Development Roadmap

- [x] Project initialization
- [ ] Phase 1: Data layer & proxy engine
- [ ] Phase 2: Regime detection & market intelligence
- [ ] Phase 3: ML & RL ensemble
- [ ] Phase 4: Signal generation & quality scoring
- [ ] Phase 5: Live monitoring & signal expiration
- [ ] Phase 6: Dashboard & API
- [ ] Phase 7: Post-trade analytics & learning
- [ ] Phase 8: Comprehensive testing
- [ ] Phase 9: Deployment & monitoring

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

## License

MIT License - See LICENSE file for details.

## Support

For issues, questions, or feature requests, please open a GitHub issue.

---

**Built with ❤️ for the Indian stock market community**
