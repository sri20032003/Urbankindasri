"""
SQLAlchemy ORM models for Urbankinda.
Covers stocks, prices, indicators, signals, trades, and performance tracking.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Stock(Base):
    """Stock master data."""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, index=True)
    name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float)  # in crores
    listing_date = Column(DateTime)
    
    # Behavioral profile
    beta = Column(Float)
    liquidity_score = Column(Float)  # 0-100
    avg_volume = Column(Float)
    avg_spread_bps = Column(Float)
    volatility = Column(Float)  # Annualized
    
    # Historical behavior
    trend_tendency = Column(Float)  # 0-100, how likely to trend
    mean_reversion_tendency = Column(Float)  # 0-100
    momentum_tendency = Column(Float)  # 0-100
    gap_tendency = Column(Float)  # 0-100
    breakout_tendency = Column(Float)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_data_fetch = Column(DateTime)
    
    # Relationships
    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="stock", cascade="all, delete-orphan")
    proxies = relationship("ProxyValue", back_populates="stock", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_stock_symbol_date', 'symbol'),
    )

class Price(Base):
    """OHLCV price data."""
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(String(20))  # 1m, 5m, 15m, 1h, 1d, 1w
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    vwap = Column(Float)
    
    # Data quality
    source = Column(String(50))  # yfinance, zerodha, nse_api, etc.
    quality_score = Column(Float)  # 0-100
    freshness_score = Column(Float)  # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    __table_args__ = (
        Index('ix_price_stock_timestamp', 'stock_id', 'timestamp'),
        Index('ix_price_stock_timeframe', 'stock_id', 'timeframe'),
    )

class Indicator(Base):
    """Calculated technical indicator values."""
    __tablename__ = "indicators"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(String(20))
    
    # Indicator values (JSON for flexibility)
    indicator_name = Column(String(50))  # RSI, MACD, EMA, ADX, etc.
    values = Column(JSON)  # {"value": 45.5, "direction": "up", "strength": 0.8}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_indicator_stock_timestamp', 'stock_id', 'timestamp'),
    )

class ProxyValue(Base):
    """Observable proxy values for signal generation."""
    __tablename__ = "proxy_values"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(String(20))
    
    # Proxy information
    proxy_name = Column(String(100))  # relative_strength, breakout_volume, etc.
    proxy_category = Column(String(50))  # price_action, volume, momentum, etc.
    
    # Proxy output
    value = Column(Float)
    direction = Column(String(20))  # up, down, neutral
    strength = Column(Float)  # 0-1
    reliability = Column(Float)  # 0-1, based on historical accuracy
    regime_suitability = Column(String(50))  # strong_bull, sideways, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="proxies")
    
    __table_args__ = (
        Index('ix_proxy_stock_timestamp', 'stock_id', 'timestamp'),
        Index('ix_proxy_name', 'proxy_name'),
    )

class MarketRegime(Base):
    """Market regime classification."""
    __tablename__ = "market_regimes"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Regime classification
    market_regime = Column(String(50))  # STRONG_BULL, WEAK_BULL, SIDEWAYS, WEAK_BEAR, STRONG_BEAR
    volatility_regime = Column(String(50))  # LOW, NORMAL, HIGH, EXTREME
    trend_classification = Column(String(50))  # TREND, RANGE, BREAKOUT, BREAKDOWN, TRANSITION
    
    # Supporting metrics
    vix_level = Column(Float)
    nifty_momentum = Column(Float)  # 0-1
    market_breadth = Column(Float)  # advance/decline ratio
    sector_momentum = Column(Float)  # average sector momentum
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    """Generated trade signals."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Signal details
    action = Column(String(20))  # BUY, SELL, HOLD, WAIT, NO_TRADE
    confidence = Column(Float)  # 0-1
    uncertainty = Column(String(50))  # LOW, MEDIUM, HIGH
    quality_score = Column(Float)  # 0-100
    
    # Setup information
    selected_setup = Column(String(500))  # Comma-separated proxy/indicator names
    market_regime = Column(String(50))
    volatility_regime = Column(String(50))
    
    # Entry/Stop/Target
    entry_price = Column(Float)
    entry_zone_low = Column(Float)
    entry_zone_high = Column(Float)
    stop_loss = Column(Float)
    target_1 = Column(Float)
    target_2 = Column(Float)
    target_3 = Column(Float)
    
    # Risk/Reward
    risk = Column(Float)  # Entry - Stop Loss
    reward = Column(Float)  # Target - Entry
    risk_reward_ratio = Column(Float)  # Reward / Risk
    
    # Model outputs
    ml_probability = Column(Float)  # 0-1
    rl_probability = Column(Float)  # 0-1
    model_agreement = Column(Float)  # 0-1
    
    # Supporting evidence
    top_supporting_proxies = Column(JSON)  # List of proxy names
    top_risks = Column(JSON)  # List of risk factors
    
    # Signal lifecycle
    is_active = Column(Boolean, default=True)
    validity_until = Column(DateTime)
    invalidation_reason = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="signals")
    outcome = relationship("SignalOutcome", back_populates="signal", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_signal_stock_timestamp', 'stock_id', 'timestamp'),
        Index('ix_signal_active', 'is_active'),
    )

class SignalOutcome(Base):
    """Actual trade outcome for learning."""
    __tablename__ = "signal_outcomes"
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=False)
    
    # Actual execution
    actual_entry = Column(Float)
    actual_exit = Column(Float)
    exit_reason = Column(String(100))  # TARGET_1, STOP_LOSS, SIGNAL_INVALID, MANUAL
    
    # Metrics
    holding_time_minutes = Column(Integer)
    pnl = Column(Float)  # Profit/Loss amount
    pnl_pct = Column(Float)  # Profit/Loss %
    mfe = Column(Float)  # Maximum Favorable Excursion
    mae = Column(Float)  # Maximum Adverse Excursion
    slippage_bps = Column(Float)  # Basis points
    
    # Analysis
    was_profitable = Column(Boolean)
    quality_validation = Column(Float)  # Was signal quality score accurate?
    proxy_accuracy = Column(JSON)  # {"proxy_name": accuracy_score}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    signal = relationship("Signal", back_populates="outcome")
    
    __table_args__ = (
        Index('ix_outcome_signal', 'signal_id'),
    )

class StrategyPerformance(Base):
    """Track performance of indicator combinations."""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True)
    
    # Strategy identification
    strategy_name = Column(String(200))  # e.g., "EMA+ADX+VWAP+Volume"
    strategy_hash = Column(String(64), unique=True, index=True)
    
    stock = Column(String(20))
    market_regime = Column(String(50))
    volatility_regime = Column(String(50))
    
    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    win_rate = Column(Float)  # 0-1
    profit_factor = Column(Float)
    expectancy = Column(Float)  # Average P&L per trade
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    avg_win = Column(Float)
    avg_loss = Column(Float)
    avg_holding_time_minutes = Column(Float)
    
    # Robustness metrics
    out_of_sample_performance = Column(Float)
    stability_score = Column(Float)  # 0-1
    overfitting_score = Column(Float)  # 0-1, lower is better
    
    # Recent performance
    last_trade_date = Column(DateTime)
    recent_accuracy = Column(Float)  # Last N trades accuracy
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_strategy_stock_regime', 'stock', 'market_regime'),
    )

class ProxyReliability(Base):
    """Track proxy usefulness from post-trade analysis."""
    __tablename__ = "proxy_reliability"
    
    id = Column(Integer, primary_key=True)
    proxy_name = Column(String(100), unique=True, index=True)
    proxy_category = Column(String(50))
    
    # Historical performance
    total_signals = Column(Integer, default=0)
    correct_signals = Column(Integer, default=0)
    accuracy = Column(Float)  # 0-1
    
    # Regime-specific accuracy
    accuracy_strong_bull = Column(Float)
    accuracy_weak_bull = Column(Float)
    accuracy_sideways = Column(Float)
    accuracy_weak_bear = Column(Float)
    accuracy_strong_bear = Column(Float)
    
    # Degradation detection
    recent_accuracy = Column(Float)  # Last 30 trades
    accuracy_trend = Column(String(20))  # up, down, stable
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelPerformance(Base):
    """Track ML/RL model performance."""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True)
    
    model_name = Column(String(100))  # XGBoost, LSTM, PPO, etc.
    model_version = Column(String(50))
    
    # Performance metrics
    accuracy = Column(Float)  # 0-1
    precision = Column(Float)  # 0-1
    recall = Column(Float)  # 0-1
    f1_score = Column(Float)  # 0-1
    calibration = Column(Float)  # How well-calibrated predictions are
    
    # Trading metrics
    expected_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    
    # Regime-specific performance
    performance_strong_bull = Column(Float)
    performance_weak_bull = Column(Float)
    performance_sideways = Column(Float)
    performance_weak_bear = Column(Float)
    performance_strong_bear = Column(Float)
    
    # Recent performance
    recent_accuracy = Column(Float)  # Last N predictions
    accuracy_trend = Column(String(20))  # up, down, stable
    
    last_trained = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_model_name_version', 'model_name', 'model_version'),
    )

class BacktestResult(Base):
    """Store backtest and walk-forward validation results."""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True)
    
    test_name = Column(String(200))
    strategy_name = Column(String(200))
    stock = Column(String(20))
    
    # Backtest period
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    train_start = Column(DateTime)
    train_end = Column(DateTime)
    test_start = Column(DateTime)
    test_end = Column(DateTime)
    
    # Results
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_return = Column(Float)  # %
    annualized_return = Column(Float)  # %
    max_drawdown = Column(Float)  # %
    sharpe_ratio = Column(Float)
    
    # Validation flags
    has_lookahead_bias = Column(Boolean, default=False)
    overfitting_detected = Column(Boolean, default=False)
    overfitting_score = Column(Float)  # 0-1
    
    # Detailed results
    trades_log = Column(JSON)  # List of trade details
    metrics_log = Column(JSON)  # Detailed metrics
    
    created_at = Column(DateTime, default=datetime.utcnow)
