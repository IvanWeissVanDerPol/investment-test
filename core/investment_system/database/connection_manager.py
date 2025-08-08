"""
Database Connection Manager
Handles PostgreSQL and SQLite connections with connection pooling
"""

import logging
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2 import sql, OperationalError
import sqlite3

from ..utils.secure_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    Manages database connections with automatic failover from PostgreSQL to SQLite
    """
    
    def __init__(self):
        """Initialize database connection manager"""
        self.config = get_config_manager()
        self.db_config = self.config.get_database_config()
        
        self._engine = None
        self._session_factory = None
        self._is_postgresql = False
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection with failover"""
        
        # Try PostgreSQL first
        try:
            self._engine = self._create_postgresql_engine()
            self._test_connection()
            self._session_factory = sessionmaker(bind=self._engine)
            self._is_postgresql = True
            logger.info("Connected to PostgreSQL database")
            return
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
        
        # Fallback to SQLite
        try:
            self._engine = self._create_sqlite_engine()
            self._test_connection()
            self._session_factory = sessionmaker(bind=self._engine)
            self._is_postgresql = False
            logger.info("Connected to SQLite database (fallback)")
        except Exception as e:
            logger.error(f"All database connections failed: {e}")
            raise ConnectionError("Could not establish database connection")
    
    def _create_postgresql_engine(self):
        """Create PostgreSQL engine with connection pooling"""
        
        # Parse DATABASE_URL or construct from components
        database_url = self.db_config.url
        
        if not database_url.startswith('postgresql://'):
            raise ValueError("Invalid PostgreSQL URL format")
        
        # Create engine with connection pooling
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.db_config.pool_size,
            max_overflow=self.db_config.max_overflow,
            pool_timeout=self.db_config.pool_timeout,
            pool_recycle=3600,  # Recycle connections every hour
            echo=self.config.is_development(),  # Log SQL in development
            connect_args={
                "connect_timeout": 10,
                "options": "-c timezone=utc"
            }
        )
        
        return engine
    
    def _create_sqlite_engine(self):
        """Create SQLite engine for fallback"""
        
        sqlite_path = self.db_config.sqlite_path or "core/database/investment_system.db"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        
        # Create engine
        engine = create_engine(
            f"sqlite:///{sqlite_path}",
            poolclass=StaticPool,
            pool_pre_ping=True,
            echo=self.config.is_development(),
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            }
        )
        
        return engine
    
    def _test_connection(self):
        """Test database connection"""
        with self._engine.connect() as conn:
            if self._is_postgresql:
                result = conn.execute(text("SELECT version()"))
            else:
                result = conn.execute(text("SELECT sqlite_version()"))
            
            version_info = result.fetchone()[0]
            logger.info(f"Database connection test successful: {version_info}")
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute raw SQL query"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                if result.returns_rows:
                    return result.fetchall()
                return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            inspector = inspect(self._engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> list:
        """Get table column information"""
        try:
            inspector = inspect(self._engine)
            return inspector.get_columns(table_name)
        except Exception as e:
            logger.error(f"Error getting table columns: {e}")
            return []
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Backup database (SQLite only)"""
        if self._is_postgresql:
            logger.warning("PostgreSQL backup requires external tools (pg_dump)")
            return False
        
        try:
            if not backup_path:
                backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # SQLite backup
            source = sqlite3.connect(self.db_config.sqlite_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            
            source.close()
            backup.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def create_database_if_not_exists(self, database_name: str) -> bool:
        """Create PostgreSQL database if it doesn't exist"""
        if not self._is_postgresql:
            return True  # SQLite creates database automatically
        
        try:
            # Parse connection URL to get connection without database
            url_parts = self.db_config.url.replace('postgresql://', '').split('/')
            connection_part = url_parts[0]
            
            # Connect to postgres database to create new database
            admin_url = f"postgresql://{connection_part}/postgres"
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            
            with admin_engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": database_name}
                )
                
                if not result.fetchone():
                    # Create database
                    conn.execute(
                        text(f"CREATE DATABASE {database_name}")
                    )
                    logger.info(f"Created database: {database_name}")
                else:
                    logger.info(f"Database already exists: {database_name}")
            
            admin_engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database {database_name}: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'engine_type': 'PostgreSQL' if self._is_postgresql else 'SQLite',
            'url': self.db_config.url if self._is_postgresql else f"sqlite:///{self.db_config.sqlite_path}",
            'pool_size': self.db_config.pool_size if self._is_postgresql else 'N/A',
            'is_connected': self._engine is not None
        }
    
    def close_connections(self):
        """Close all database connections"""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
    
    @property 
    def engine(self):
        """Get SQLAlchemy engine"""
        return self._engine
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return self._is_postgresql


# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None


def get_connection_manager() -> DatabaseConnectionManager:
    """Get the global database connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = DatabaseConnectionManager()
    return _connection_manager


@contextmanager
def get_db_session():
    """Convenience function to get database session"""
    manager = get_connection_manager()
    with manager.get_session() as session:
        yield session


def get_db_connection():
    """Get database connection (for backward compatibility)"""
    manager = get_connection_manager()
    return manager.engine.connect()


def test_database_connection() -> bool:
    """Test database connection"""
    try:
        manager = get_connection_manager()
        manager._test_connection()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    
    try:
        manager = DatabaseConnectionManager()
        info = manager.get_connection_info()
        
        print(f"Connection Info: {info}")
        
        # Test session
        with manager.get_session() as session:
            if manager.is_postgresql:
                result = session.execute(text("SELECT current_database()"))
            else:
                result = session.execute(text("SELECT 'SQLite' as db"))
            
            db_name = result.fetchone()[0]
            print(f"Connected to database: {db_name}")
        
        print("Database connection test successful!")
        
    except Exception as e:
        print(f"Database connection test failed: {e}")
    
    finally:
        if 'manager' in locals():
            manager.close_connections()