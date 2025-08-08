"""
Secure Configuration Manager
Handles environment variables, secrets, and secure configuration loading
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
import base64
import secrets

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    sqlite_path: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


@dataclass
class APIConfig:
    """API configuration"""
    alpha_vantage_key: str
    twelvedata_key: str
    polygon_key: str
    finnhub_key: str
    newsapi_key: str
    youtube_key: str
    claude_key: str


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    encryption_key: str
    jwt_secret: str
    enable_https: bool = False
    session_timeout: int = 3600  # 1 hour


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    per_minute: int = 60
    per_hour: int = 1000
    per_day: int = 10000


class SecureConfigManager:
    """
    Secure configuration manager that handles environment variables,
    encrypted secrets, and configuration validation
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize secure configuration manager"""
        # Delegate loading and validation to centralized settings
        self.settings = get_settings()
        self.environment = self.settings.environment
        self._cipher_suite = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive data"""
    encryption_key = self.settings.security.encryption_key
        if encryption_key:
            try:
                # Validate and decode the encryption key
                key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
                self._cipher_suite = Fernet(base64.urlsafe_b64encode(key_bytes))
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
                self._cipher_suite = None
        else:
            logger.warning("No encryption key provided - encrypted values will not be available")
    
    @classmethod
    def generate_encryption_key(cls) -> str:
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
    
    @classmethod
    def generate_secret_key(cls) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)
    
    def get_secure_value(self, key: str, encrypted: bool = False) -> str:
        """Get a secure configuration value from settings by env-style key name."""
        # Map common env keys to settings attributes
        mapping = {
            # Database
            'DATABASE_URL': self.settings.database.database_url,
            'SQLITE_DB_PATH': self.settings.database.sqlite_db_path or '',
            'DB_POOL_SIZE': str(self.settings.database.db_pool_size),
            'DB_MAX_OVERFLOW': str(self.settings.database.db_max_overflow),
            'DB_POOL_TIMEOUT': str(self.settings.database.db_pool_timeout),
            # APIs
            'ALPHA_VANTAGE_API_KEY': self.settings.apis.alpha_vantage_api_key or '',
            'TWELVEDATA_API_KEY': self.settings.apis.twelvedata_api_key or '',
            'POLYGON_API_KEY': self.settings.apis.polygon_api_key or '',
            'FINNHUB_API_KEY': self.settings.apis.finnhub_api_key or '',
            'NEWSAPI_KEY': self.settings.apis.newsapi_key or '',
            'YOUTUBE_API_KEY': self.settings.apis.youtube_api_key or '',
            'CLAUDE_API_KEY': self.settings.apis.claude_api_key or '',
            'ALPACA_API_KEY': self.settings.apis.alpaca_api_key or '',
            'ALPACA_API_SECRET': self.settings.apis.alpaca_api_secret or '',
            # Security
            'SECRET_KEY': self.settings.security.secret_key,
            'ENCRYPTION_KEY': self.settings.security.encryption_key,
            'JWT_SECRET_KEY': self.settings.security.jwt_secret_key,
            'ENABLE_HTTPS': 'true' if self.settings.security.enable_https else 'false',
            'SESSION_TIMEOUT': str(self.settings.security.session_timeout),
            # Redis
            'REDIS_URL': self.settings.redis.redis_url,
            # Log
            'LOG_LEVEL': self.settings.log_level,
            'ENVIRONMENT': self.settings.environment,
        }

        if key not in mapping or mapping[key] == '':
            raise ValueError(f"Required configuration value '{key}' not available in settings")

        value = mapping[key]
        if encrypted and self._cipher_suite:
            try:
                decrypted_bytes = self._cipher_suite.decrypt(value.encode())
                return decrypted_bytes.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt value for key '{key}': {e}")
                raise ValueError(f"Invalid encrypted value for key '{key}'")
        return value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return DatabaseConfig(
            url=self.settings.database.database_url,
            sqlite_path=self.settings.database.sqlite_db_path,
            pool_size=self.settings.database.db_pool_size,
            max_overflow=self.settings.database.db_max_overflow,
            pool_timeout=self.settings.database.db_pool_timeout,
        )
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return APIConfig(
            alpha_vantage_key=self.settings.apis.alpha_vantage_api_key or '',
            twelvedata_key=self.settings.apis.twelvedata_api_key or '',
            polygon_key=self.settings.apis.polygon_api_key or '',
            finnhub_key=self.settings.apis.finnhub_api_key or '',
            newsapi_key=self.settings.apis.newsapi_key or '',
            youtube_key=self.settings.apis.youtube_api_key or '',
            claude_key=self.settings.apis.claude_api_key or '',
        )
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return SecurityConfig(
            secret_key=self.settings.security.secret_key,
            encryption_key=self.settings.security.encryption_key,
            jwt_secret=self.settings.security.jwt_secret_key,
            enable_https=self.settings.security.enable_https,
            session_timeout=self.settings.security.session_timeout,
        )
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limiting configuration"""
        return RateLimitConfig(
            per_minute=self.settings.rate_limits.api_rate_limit_per_minute,
            per_hour=self.settings.rate_limits.api_rate_limit_per_hour,
            per_day=self.settings.rate_limits.api_rate_limit_per_day,
        )
    
    def get_portfolio_config(self) -> Dict[str, Any]:
        """Get portfolio configuration"""
        return {
            'default_balance': self.settings.portfolio.default_portfolio_balance,
            'default_risk_tolerance': self.settings.portfolio.default_risk_tolerance,
            'max_position_percent': self.settings.portfolio.default_max_position_percent,
            'rebalance_threshold': self.settings.portfolio.rebalance_threshold,
            'min_position_size': self.settings.portfolio.min_position_size,
        }
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate all configuration values"""
        validation_results = {}
        
        try:
            # Test database config
            db_config = self.get_database_config()
            validation_results['database'] = bool(db_config.url)
        except Exception as e:
            logger.error(f"Database configuration invalid: {e}")
            validation_results['database'] = False
        
        try:
            # Test API config
            api_config = self.get_api_config()
            validation_results['api_keys'] = all([
                api_config.alpha_vantage_key,
                api_config.claude_key,
                api_config.newsapi_key
            ])
        except Exception as e:
            logger.error(f"API configuration invalid: {e}")
            validation_results['api_keys'] = False
        
        try:
            # Test security config
            security_config = self.get_security_config()
            validation_results['security'] = all([
                len(security_config.secret_key) >= 32,
                security_config.encryption_key,
                security_config.jwt_secret
            ])
        except Exception as e:
            logger.error(f"Security configuration invalid: {e}")
            validation_results['security'] = False
        
        return validation_results
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'
    
    def get_log_level(self) -> str:
        """Get logging level"""
    return (self.settings.log_level or 'INFO').upper()


# Global configuration manager instance
_config_manager: Optional[SecureConfigManager] = None


def get_config_manager() -> SecureConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager()
    return _config_manager


def validate_environment_setup() -> bool:
    """Validate that environment is properly configured"""
    config_manager = get_config_manager()
    validation_results = config_manager.validate_configuration()
    
    all_valid = all(validation_results.values())
    
    if not all_valid:
        logger.error("Environment configuration validation failed:")
        for component, is_valid in validation_results.items():
            status = "✓" if is_valid else "✗"
            logger.error(f"  {status} {component}")
    
    return all_valid


if __name__ == "__main__":
    # Test configuration management
    print("Testing configuration management...")
    
    # Generate sample keys
    print(f"Sample encryption key: {SecureConfigManager.generate_encryption_key()}")
    print(f"Sample secret key: {SecureConfigManager.generate_secret_key()}")
    
    # Validate current environment
    is_valid = validate_environment_setup()
    print(f"Environment validation: {'PASS' if is_valid else 'FAIL'}")