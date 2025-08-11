"""
Database models and connection management.
SQLAlchemy models with security-first design.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import uuid

from sqlalchemy import (
    create_engine, Column, String, DateTime, Enum, Boolean,
    Integer, Float, JSON, ForeignKey, Index, UniqueConstraint,
    Text, DECIMAL, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects.postgresql import UUID

from investment_system.core.contracts import UserTier, SignalType
from investment_system.security.password import hash_password, verify_password

Base = declarative_base()


class User(Base):
    """User model with secure password storage"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    
    # API key management
    api_key_id = Column(String(64), unique=True, index=True)
    api_key_hash = Column(String(255))
    api_key_created_at = Column(DateTime, default=datetime.utcnow)
    api_key_last_used = Column(DateTime)
    
    # Stripe integration
    stripe_customer_id = Column(String(255), index=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255))
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    two_factor_secret = Column(String(255))
    two_factor_enabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Set hashed password"""
        self.hashed_password = hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        return verify_password(password, self.hashed_password)
    
    def __repr__(self):
        return f"<User(email={self.email}, tier={self.tier})>"


class Subscription(Base):
    """Subscription model for billing"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tier = Column(Enum(UserTier), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, expired
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    stripe_payment_method_id = Column(String(255))
    
    # Billing details
    monthly_amount = Column(Integer)  # Amount in cents
    currency = Column(String(3), default="USD")
    interval = Column(String(20), default="month")  # month, year
    
    # Dates
    started_at = Column(DateTime, default=datetime.utcnow)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancelled_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Usage limits
    api_calls_limit = Column(Integer, default=1000)
    symbols_limit = Column(Integer, default=10)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    __table_args__ = (
        Index("idx_subscription_user_status", "user_id", "status"),
    )


class APIUsage(Base):
    """Track API usage for billing and rate limiting"""
    __tablename__ = "api_usage"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Request details
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Usage metrics
    units = Column(Integer, default=1)  # Number of symbols, signals, etc.
    credits_used = Column(Integer, default=1)
    
    # Request metadata
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(String(500))
    request_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="api_usage")
    
    __table_args__ = (
        Index("idx_usage_user_created", "user_id", "created_at"),
        Index("idx_usage_endpoint", "endpoint", "created_at"),
    )


class Signal(Base):
    """Trading signals generated for users"""
    __tablename__ = "signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Signal details
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(Enum(SignalType), nullable=False)
    confidence = Column(Float, nullable=False)
    price = Column(DECIMAL(20, 8))
    
    # Indicators
    rsi = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    volume = Column(BigInteger)
    
    # Additional data
    indicators = Column(JSON)  # Store all indicators as JSON
    reasoning = Column(Text)
    ai_enhanced = Column(Boolean, default=False)
    
    # Performance tracking
    entry_price = Column(DECIMAL(20, 8))
    exit_price = Column(DECIMAL(20, 8))
    profit_loss = Column(DECIMAL(20, 8))
    accuracy = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="signals")
    
    __table_args__ = (
        Index("idx_signal_user_symbol", "user_id", "symbol", "created_at"),
        Index("idx_signal_created", "created_at"),
    )


class MarketData(Base):
    """Cached market data"""
    __tablename__ = "market_data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # OHLCV data
    timestamp = Column(DateTime, nullable=False)
    open = Column(DECIMAL(20, 8), nullable=False)
    high = Column(DECIMAL(20, 8), nullable=False)
    low = Column(DECIMAL(20, 8), nullable=False)
    close = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(BigInteger)
    
    # Metadata
    source = Column(String(50))  # yfinance, alpaca, etc.
    is_adjusted = Column(Boolean, default=True)
    
    # Cache management
    fetched_at = Column(DateTime, default=datetime.utcnow)
    ttl_seconds = Column(Integer, default=600)
    
    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", "source", name="uq_market_data"),
        Index("idx_market_symbol_time", "symbol", "timestamp"),
    )


class AuditLog(Base):
    """Security audit logging"""
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50))  # auth, api, billing, security
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(UUID(as_uuid=True))
    
    # Event data
    details = Column(JSON)
    old_value = Column(JSON)
    new_value = Column(JSON)
    
    # Security
    risk_score = Column(Integer)
    flagged = Column(Boolean, default=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_user_created", "user_id", "created_at"),
        Index("idx_audit_event_created", "event_type", "created_at"),
        Index("idx_audit_flagged", "flagged", "created_at"),
    )


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite:///runtime/investment_system.db"
        )
        
        # Configure engine with connection pooling
        engine_kwargs = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_pre_ping": True,  # Verify connections
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }
        
        # SQLite doesn't support some pool options
        if self.database_url.startswith("sqlite"):
            engine_kwargs = {"pool_pre_ping": True}
        
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            **engine_kwargs
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def __enter__(self) -> Session:
        """Context manager entry"""
        self.session = self.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Session:
    """Get database session for dependency injection"""
    db = get_db_manager().get_session()
    try:
        yield db
    finally:
        db.close()


# Async session management
class AsyncDatabaseManager:
    """Async database connection and session management"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///runtime/investment_system.db"
        )
        
        # Convert sync URL to async if needed
        if self.database_url.startswith("sqlite://"):
            self.database_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Configure async engine
        self.engine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def session(self):
        """Get async database session"""
        async with self.async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global async database manager
_async_db_manager: Optional[AsyncDatabaseManager] = None


def get_async_db_manager() -> AsyncDatabaseManager:
    """Get global async database manager instance"""
    global _async_db_manager
    if _async_db_manager is None:
        _async_db_manager = AsyncDatabaseManager()
    return _async_db_manager


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get async database session"""
    async with get_async_db_manager().session() as session:
        yield session