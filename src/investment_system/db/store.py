"""Database storage module with SQLAlchemy models and persistence."""

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    DateTime,
    Integer,
    Boolean,
    text,
    UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

# Ensure runtime directory exists
RUNTIME_DIR = Path("runtime")
RUNTIME_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{RUNTIME_DIR}/app.db"

Base = declarative_base()


class Price(Base):
    """Price data model."""
    __tablename__ = 'prices'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    ts = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'ts', name='_symbol_ts_uc'),)


class Signal(Base):
    """Trading signal model."""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    ts = Column(DateTime, nullable=False)
    signal = Column(String, nullable=False)
    rsi = Column(Float)
    sma20 = Column(Float)
    sma50 = Column(Float)
    close = Column(Float)
    is_stale = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'ts', name='_symbol_ts_signal_uc'),)


class StoreManager:
    """Database store manager with connection pooling and resilience."""
    
    def __init__(self):
        """Initialize database connection and create tables."""
        self.engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},  # SQLite specific
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Apply pragmas for performance
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.commit()
        
        # Create tables if not exist
        Base.metadata.create_all(self.engine)
        
        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Initialized database at {DATABASE_URL}")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    def upsert_signals(self, signals: List[Dict[str, Any]]) -> int:
        """
        Upsert signals to database.
        
        Args:
            signals: List of signal dictionaries
        
        Returns:
            Number of signals upserted
        """
        count = 0
        
        with self.get_session() as session:
            try:
                for signal_data in signals:
                    # Parse timestamp
                    ts = datetime.fromisoformat(signal_data['ts'].replace('Z', '+00:00'))
                    
                    # Check if signal exists
                    existing = session.query(Signal).filter(
                        Signal.symbol == signal_data['symbol'],
                        Signal.ts == ts
                    ).first()
                    
                    if existing:
                        # Update existing signal
                        existing.signal = signal_data['signal']
                        existing.rsi = signal_data.get('rsi')
                        existing.sma20 = signal_data.get('sma20')
                        existing.sma50 = signal_data.get('sma50')
                        existing.close = signal_data.get('close')
                        existing.is_stale = signal_data.get('is_stale', False)
                    else:
                        # Create new signal
                        new_signal = Signal(
                            symbol=signal_data['symbol'],
                            ts=ts,
                            signal=signal_data['signal'],
                            rsi=signal_data.get('rsi'),
                            sma20=signal_data.get('sma20'),
                            sma50=signal_data.get('sma50'),
                            close=signal_data.get('close'),
                            is_stale=signal_data.get('is_stale', False)
                        )
                        session.add(new_signal)
                    
                    count += 1
                
                session.commit()
                logger.info(f"Upserted {count} signals")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to upsert signals: {e}")
                raise
        
        return count
    
    def get_latest_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get latest signals from database.
        
        Args:
            limit: Maximum number of signals to return
        
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        with self.get_session() as session:
            try:
                results = session.query(Signal)\
                    .order_by(Signal.ts.desc())\
                    .limit(limit)\
                    .all()
                
                for signal in results:
                    signals.append({
                        'symbol': signal.symbol,
                        'ts': signal.ts.isoformat(),
                        'signal': signal.signal,
                        'rsi': signal.rsi,
                        'sma20': signal.sma20,
                        'sma50': signal.sma50,
                        'close': signal.close,
                        'is_stale': signal.is_stale,
                        'created_at': signal.created_at.isoformat()
                    })
                
                logger.info(f"Retrieved {len(signals)} signals")
                
            except Exception as e:
                logger.error(f"Failed to get signals: {e}")
                raise
        
        return signals
    
    def upsert_prices(self, prices_df) -> int:
        """
        Upsert price data to database.
        
        Args:
            prices_df: DataFrame with price data
        
        Returns:
            Number of price records upserted
        """
        count = 0
        
        with self.get_session() as session:
            try:
                for _, row in prices_df.iterrows():
                    ts = datetime.combine(row['date'], datetime.min.time())
                    
                    # Check if price exists
                    existing = session.query(Price).filter(
                        Price.symbol == row['symbol'],
                        Price.ts == ts
                    ).first()
                    
                    if existing:
                        # Update existing price
                        existing.open = row['open']
                        existing.high = row['high']
                        existing.low = row['low']
                        existing.close = row['close']
                        existing.volume = row['volume']
                    else:
                        # Create new price
                        new_price = Price(
                            symbol=row['symbol'],
                            ts=ts,
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            volume=row['volume']
                        )
                        session.add(new_price)
                    
                    count += 1
                
                session.commit()
                logger.info(f"Upserted {count} price records")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to upsert prices: {e}")
                raise
        
        return count


# Global instance
_store: Optional[StoreManager] = None


def get_store() -> StoreManager:
    """Get or create the global store instance."""
    global _store
    if _store is None:
        _store = StoreManager()
    return _store