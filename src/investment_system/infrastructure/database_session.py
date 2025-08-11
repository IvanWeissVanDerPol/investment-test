"""
Unified database session management with proper async support and connection pooling.
Replaces scattered database initialization and provides consistent session handling.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy import text, event
from sqlalchemy.orm import DeclarativeBase

from config.settings import get_settings
from investment_system.core.logging import get_logger
from investment_system.core.exceptions import APIError, ErrorCode

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class DatabaseManager:
    """
    Centralized database manager with async support, connection pooling,
    and proper error handling.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._is_initialized = False
        self._connection_retries = 3
        self._retry_delay = 1.0
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._is_initialized:
            return
        
        try:
            # Parse database URL to determine database type
            parsed_url = urlparse(self.settings.database_url)
            db_type = parsed_url.scheme.split('+')[0]  # Handle async drivers like sqlite+aiosqlite
            
            # Configure engine based on database type
            if db_type == 'sqlite':
                self._engine = await self._create_sqlite_engine()
            elif db_type in ['postgresql', 'postgres']:
                self._engine = await self._create_postgresql_engine()
            elif db_type == 'mysql':
                self._engine = await self._create_mysql_engine()
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test connection
            await self._test_connection()
            
            self._is_initialized = True
            logger.info(
                "Database initialized successfully",
                database_type=db_type,
                url_host=parsed_url.hostname or "local"
            )
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise APIError(
                ErrorCode.DATABASE_ERROR,
                f"Database initialization failed: {str(e)}"
            ) from e
    
    async def _create_sqlite_engine(self) -> AsyncEngine:
        """Create SQLite async engine with optimized settings."""
        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        if not self.settings.database_url.startswith('sqlite+aiosqlite://'):
            url = self.settings.database_url.replace('sqlite://', 'sqlite+aiosqlite://')
        else:
            url = self.settings.database_url
        
        engine = create_async_engine(
            url,
            echo=self.settings.debug,
            poolclass=StaticPool,
            pool_pre_ping=True,
            pool_recycle=300,  # 5 minutes
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            }
        )
        
        # Configure SQLite for better performance and concurrency
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set cache size (negative means KB)
            cursor.execute("PRAGMA cache_size=-32000")  # 32MB
            # Set temp store to memory
            cursor.execute("PRAGMA temp_store=memory")
            cursor.close()
        
        return engine
    
    async def _create_postgresql_engine(self) -> AsyncEngine:
        """Create PostgreSQL async engine with connection pooling."""
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        if not self.settings.database_url.startswith('postgresql+asyncpg://'):
            url = self.settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        else:
            url = self.settings.database_url
        
        return create_async_engine(
            url,
            echo=self.settings.debug,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
            pool_timeout=30,
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for better connection time
                }
            }
        )
    
    async def _create_mysql_engine(self) -> AsyncEngine:
        """Create MySQL async engine with connection pooling."""
        # Convert mysql:// to mysql+aiomysql:// for async support
        if not self.settings.database_url.startswith('mysql+aiomysql://'):
            url = self.settings.database_url.replace('mysql://', 'mysql+aiomysql://')
        else:
            url = self.settings.database_url
        
        return create_async_engine(
            url,
            echo=self.settings.debug,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
            pool_timeout=30
        )
    
    async def _test_connection(self) -> None:
        """Test database connection with retry logic."""
        for attempt in range(self._connection_retries):
            try:
                async with self._engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                return
            except Exception as e:
                if attempt < self._connection_retries - 1:
                    logger.warning(
                        f"Database connection test failed (attempt {attempt + 1}/{self._connection_retries})",
                        error=str(e)
                    )
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with automatic cleanup and error handling.
        
        Usage:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        if not self._is_initialized:
            await self.initialize()
        
        if not self._session_factory:
            raise APIError(
                ErrorCode.DATABASE_ERROR,
                "Database not properly initialized"
            )
        
        session = self._session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise APIError(
                ErrorCode.DATABASE_ERROR,
                f"Database operation failed: {str(e)}"
            ) from e
        except Exception as e:
            await session.rollback()
            logger.error("Unexpected session error", error=str(e))
            raise
        finally:
            await session.close()
    
    async def execute_with_retry(
        self,
        operation: callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute database operation with automatic retry on connection errors.
        
        Args:
            operation: Async function to execute
            *args: Arguments for the operation
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            APIError: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except (DisconnectionError, ConnectionError, OSError) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s",
                        error=str(e)
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Database operation failed after {max_retries + 1} attempts",
                        error=str(e)
                    )
            except SQLAlchemyError as e:
                # Don't retry on other SQLAlchemy errors
                logger.error("Database operation failed with non-retryable error", error=str(e))
                raise APIError(
                    ErrorCode.DATABASE_ERROR,
                    f"Database operation failed: {str(e)}"
                ) from e
        
        # If we get here, all retries failed
        raise APIError(
            ErrorCode.CONNECTION_ERROR,
            f"Database operation failed after {max_retries + 1} attempts: {str(last_exception)}"
        ) from last_exception
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Dictionary with health check results
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection_pool": self._get_pool_status()
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_pool": self._get_pool_status()
            }
    
    def _get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status information."""
        if not self._engine:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "size": getattr(pool, 'size', lambda: 'unknown')(),
            "checked_in": getattr(pool, 'checkedin', lambda: 'unknown')(),
            "checked_out": getattr(pool, 'checkedout', lambda: 'unknown')(),
            "overflow": getattr(pool, 'overflow', lambda: 'unknown')(),
            "invalid": getattr(pool, 'invalid', lambda: 'unknown')()
        }
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            raise APIError(ErrorCode.DATABASE_ERROR, "Database not initialized")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise APIError(
                ErrorCode.DATABASE_ERROR,
                f"Failed to create tables: {str(e)}"
            ) from e
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        if not self._engine:
            raise APIError(ErrorCode.DATABASE_ERROR, "Database not initialized")
        
        if self.settings.environment == "production":
            raise APIError(
                ErrorCode.AUTHORIZATION_FAILED,
                "Cannot drop tables in production environment"
            )
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error("Failed to drop database tables", error=str(e))
            raise APIError(
                ErrorCode.DATABASE_ERROR,
                f"Failed to drop tables: {str(e)}"
            ) from e
    
    async def close(self) -> None:
        """Close database engine and clean up resources."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            logger.info("Database connection closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience function to get a database session.
    
    Usage:
        async with get_database_session() as session:
            result = await session.execute(query)
            await session.commit()
    """
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session


async def execute_with_retry(operation: callable, *args, **kwargs) -> Any:
    """
    Convenience function to execute database operations with retry logic.
    
    Args:
        operation: Async function to execute
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Result of the operation
    """
    db_manager = get_database_manager()
    return await db_manager.execute_with_retry(operation, *args, **kwargs)


async def initialize_database() -> None:
    """Initialize the database system."""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database() -> None:
    """Close the database system."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


# Context manager for database transactions
@asynccontextmanager
async def database_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database transactions with automatic rollback on error.
    
    Usage:
        async with database_transaction() as session:
            # Perform multiple operations
            await session.execute(query1)
            await session.execute(query2)
            # Transaction is automatically committed on success
            # or rolled back on exception
    """
    async with get_database_session() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            # Session.begin() automatically rolls back on exception
            raise