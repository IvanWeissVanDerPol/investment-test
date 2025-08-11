"""
Modular time-series database models optimized for compute efficiency.
Uses partitioning, indexing, and granularity optimization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, DateTime, Date, Enum as SQLEnum, Boolean,
    Integer, Float, JSON, ForeignKey, Index, UniqueConstraint,
    Text, DECIMAL, BigInteger, SmallInteger, CheckConstraint,
    PrimaryKeyConstraint, ForeignKeyConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

Base = declarative_base()


class TimeFrame(str, Enum):
    """Supported timeframes for data granularity"""
    TICK = "tick"
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class AssetClass(str, Enum):
    """Asset classification"""
    EQUITY = "equity"
    FUTURES = "futures"
    OPTIONS = "options"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    INDEX = "index"


class DataQuality(str, Enum):
    """Data quality tiers for compute optimization"""
    BRONZE = "bronze"  # Raw data
    SILVER = "silver"  # Reconciled, cleaned
    GOLD = "gold"     # Feature-engineered, ML-ready


class SecurityMaster(Base):
    """
    Master security reference data.
    Immutable reference data cached aggressively.
    """
    __tablename__ = "security_master"
    
    # Primary identification
    id = Column(String(32), primary_key=True)  # e.g., "AAPL:US"
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    
    # Security details
    isin = Column(String(12), index=True)
    cusip = Column(String(9))
    sedol = Column(String(7))
    
    # Classification
    asset_class = Column(SQLEnum(AssetClass), nullable=False, index=True)
    sector = Column(String(50))
    industry = Column(String(50))
    
    # Trading specifications
    currency = Column(String(3), nullable=False)
    tick_size = Column(DECIMAL(10, 6), default=0.01)
    lot_size = Column(Integer, default=1)
    min_trade_size = Column(Integer, default=1)
    
    # Market hours (JSON for flexibility)
    market_hours = Column(JSON)  # {"open": "09:30", "close": "16:00", "timezone": "America/New_York"}
    
    # Futures-specific
    contract_size = Column(Integer)
    expiry_date = Column(Date)
    first_notice_date = Column(Date)
    roll_method = Column(String(20))  # back_adjusted, ratio_adjusted
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    market_data = relationship("MarketDataBar", back_populates="security", cascade="all, delete-orphan")
    features = relationship("FeatureSet", back_populates="security", cascade="all, delete-orphan")
    signals = relationship("TradingSignal", back_populates="security", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_security_active_class", "is_active", "asset_class"),
        Index("idx_security_symbol_exchange", "symbol", "exchange"),
    )


class MarketDataBar(Base):
    """
    Partitioned market data bars for efficient time-series queries.
    Partitioned by symbol and date for optimal compute.
    """
    __tablename__ = "market_data_bars"
    
    # Composite primary key for partitioning
    symbol_id = Column(String(32), ForeignKey("security_master.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(SQLEnum(TimeFrame), nullable=False)
    
    # OHLCV data
    open = Column(DECIMAL(20, 8), nullable=False)
    high = Column(DECIMAL(20, 8), nullable=False)
    low = Column(DECIMAL(20, 8), nullable=False)
    close = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(BigInteger, default=0)
    
    # Advanced metrics
    vwap = Column(DECIMAL(20, 8))  # Volume-weighted average price
    trades = Column(Integer)        # Number of trades
    
    # Data quality
    quality = Column(SQLEnum(DataQuality), default=DataQuality.BRONZE)
    source = Column(String(20))  # yfinance, alpaca, polygon, etc.
    
    # Multi-source reconciliation
    n_sources = Column(SmallInteger, default=1)
    outlier_score = Column(Float)  # 0-1, higher = more likely outlier
    is_stale = Column(Boolean, default=False)
    latency_ms = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("SecurityMaster", back_populates="market_data")
    
    __table_args__ = (
        PrimaryKeyConstraint("symbol_id", "timestamp", "timeframe"),
        Index("idx_market_symbol_time_tf", "symbol_id", "timestamp", "timeframe"),
        Index("idx_market_quality_time", "quality", "timestamp"),
        Index("idx_market_partition", "symbol_id", "timestamp", postgresql_using="brin"),  # BRIN index for time-series
        CheckConstraint("high >= low", name="check_high_low"),
        CheckConstraint("high >= open", name="check_high_open"),
        CheckConstraint("high >= close", name="check_high_close"),
        CheckConstraint("low <= open", name="check_low_open"),
        CheckConstraint("low <= close", name="check_low_close"),
    )


class FeatureSet(Base):
    """
    Pre-computed features for ML models.
    Stored separately to avoid recomputation.
    """
    __tablename__ = "feature_sets"
    
    # Composite key
    symbol_id = Column(String(32), ForeignKey("security_master.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(SQLEnum(TimeFrame), nullable=False)
    feature_version = Column(String(20), nullable=False, default="v1")
    
    # Technical indicators (stored as JSON for flexibility)
    technical_features = Column(JSONB)  # {"rsi_14": 58.3, "atr_14": 1.12, "ema_20": 76.2}
    
    # Cross-sectional features
    cross_sectional = Column(JSONB)  # {"momentum_rank": 0.84, "volatility_rank": 0.22}
    
    # Regime features
    regime = Column(String(20))  # trend, mean_reversion, stress
    regime_probability = Column(JSONB)  # {"trend": 0.7, "mean_reversion": 0.2, "stress": 0.1}
    
    # Market microstructure
    microstructure = Column(JSONB)  # {"spread_bps": 1.9, "adv_pct": 0.008}
    
    # Quality flag
    quality = Column(SQLEnum(DataQuality), default=DataQuality.SILVER)
    is_complete = Column(Boolean, default=True)
    
    # Metadata
    computed_at = Column(DateTime, default=datetime.utcnow)
    compute_time_ms = Column(Integer)
    
    # Relationships
    security = relationship("SecurityMaster", back_populates="features")
    
    __table_args__ = (
        PrimaryKeyConstraint("symbol_id", "timestamp", "timeframe", "feature_version"),
        Index("idx_features_lookup", "symbol_id", "timestamp", "timeframe"),
        Index("idx_features_regime", "regime", "timestamp"),
        Index("idx_features_partition", "symbol_id", "timestamp", postgresql_using="brin"),
    )


class TradingSignal(Base):
    """
    ML-generated trading signals with risk metrics.
    Optimized for fast retrieval of latest signals.
    """
    __tablename__ = "trading_signals"
    
    # Unique signal ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Signal identification
    symbol_id = Column(String(32), ForeignKey("security_master.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(SQLEnum(TimeFrame), nullable=False)
    
    # Signal details
    direction = Column(String(10), nullable=False)  # buy, sell, hold
    score = Column(Float, nullable=False)  # Raw model output
    probability_up = Column(Float)  # Calibrated probability
    confidence = Column(Float)  # Model confidence 0-1
    
    # Expected returns
    expected_return = Column(Float)
    horizon_bars = Column(Integer)  # Prediction horizon in bars
    
    # Risk metrics
    target_volatility = Column(Float)
    realized_volatility = Column(Float)
    kelly_fraction = Column(Float)
    suggested_size = Column(Float)  # As fraction of portfolio
    
    # Model information
    model_id = Column(String(50), nullable=False)
    model_version = Column(String(20))
    ensemble_weights = Column(JSONB)  # {"lgbm": 0.4, "tft": 0.6}
    
    # Performance tracking
    is_executed = Column(Boolean, default=False)
    execution_price = Column(DECIMAL(20, 8))
    realized_pnl = Column(DECIMAL(20, 8))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    security = relationship("SecurityMaster", back_populates="signals")
    
    __table_args__ = (
        Index("idx_signals_latest", "symbol_id", "created_at", postgresql_order="DESC"),
        Index("idx_signals_confidence", "confidence", "created_at"),
        Index("idx_signals_model", "model_id", "model_version"),
        UniqueConstraint("symbol_id", "timestamp", "timeframe", "model_id", name="uq_signal"),
    )


class BacktestResult(Base):
    """
    Backtest results for strategy validation.
    Stores aggregated metrics to avoid recomputation.
    """
    __tablename__ = "backtest_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Backtest configuration
    strategy_id = Column(String(50), nullable=False, index=True)
    strategy_params = Column(JSONB, nullable=False)
    
    # Universe and period
    symbols = Column(ARRAY(String))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    timeframe = Column(SQLEnum(TimeFrame), nullable=False)
    
    # Performance metrics
    total_return = Column(Float)
    annualized_return = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    
    # Risk metrics
    value_at_risk = Column(Float)  # 95% VaR
    conditional_value_at_risk = Column(Float)  # CVaR
    
    # Detailed results (compressed)
    equity_curve = Column(JSONB)  # Time series of portfolio value
    trade_log = Column(JSONB)  # Individual trades
    
    # Validation
    is_out_of_sample = Column(Boolean, default=False)
    walk_forward_periods = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    compute_time_seconds = Column(Float)
    
    __table_args__ = (
        Index("idx_backtest_strategy", "strategy_id", "created_at"),
        Index("idx_backtest_sharpe", "sharpe_ratio", postgresql_order="DESC"),
    )


class DataSourceStatus(Base):
    """
    Track data source health and latency.
    Used for multi-source reconciliation weighting.
    """
    __tablename__ = "data_source_status"
    
    source_name = Column(String(50), primary_key=True)
    
    # Health metrics
    is_active = Column(Boolean, default=True)
    uptime_pct = Column(Float, default=100.0)
    avg_latency_ms = Column(Float)
    error_rate = Column(Float, default=0.0)
    
    # Data quality
    outlier_rate = Column(Float, default=0.0)
    staleness_rate = Column(Float, default=0.0)
    
    # Weighting for reconciliation
    reliability_score = Column(Float, default=1.0)  # 0-1, used in weighted median
    
    # Metadata
    last_success = Column(DateTime)
    last_error = Column(DateTime)
    error_message = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("reliability_score >= 0 AND reliability_score <= 1", name="check_reliability_range"),
    )


# Materialized views for performance (PostgreSQL specific)
MATERIALIZED_VIEW_SQL = """
-- Latest signals view for fast API queries
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_signals AS
SELECT DISTINCT ON (symbol_id)
    s.*,
    sm.symbol,
    sm.exchange,
    sm.asset_class
FROM trading_signals s
JOIN security_master sm ON s.symbol_id = sm.id
WHERE s.created_at > NOW() - INTERVAL '24 hours'
ORDER BY symbol_id, created_at DESC;

CREATE UNIQUE INDEX ON latest_signals (symbol_id);
CREATE INDEX ON latest_signals (created_at);

-- Feature aggregates for fast ML scoring
CREATE MATERIALIZED VIEW IF NOT EXISTS feature_aggregates AS
SELECT 
    symbol_id,
    timeframe,
    DATE_TRUNC('hour', timestamp) as hour,
    AVG((technical_features->>'rsi_14')::float) as avg_rsi,
    AVG((technical_features->>'atr_14')::float) as avg_atr,
    COUNT(*) as n_samples
FROM feature_sets
WHERE quality = 'gold'
GROUP BY symbol_id, timeframe, DATE_TRUNC('hour', timestamp);

CREATE INDEX ON feature_aggregates (symbol_id, timeframe, hour);
"""