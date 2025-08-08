"""
Secure Configuration Manager
Handles environment variables, secrets, and secure configuration loading
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
import base64
import secrets

from dotenv import load_dotenv

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
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from standard locations
            env_paths = [
                self.project_root / '.env',
                self.project_root / '.env.local',
                self.project_root / 'config' / '.env'
            ]
            
            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"Loaded environment variables from {env_path}")
                    break
        
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self._cipher_suite = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive data"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
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
        """Get a secure configuration value"""
        value = os.getenv(key)
        
        if not value:
            raise ValueError(f"Required configuration value '{key}' not found in environment")
        
        if encrypted and self._cipher_suite:
            try:
                # Decrypt the value
                decrypted_bytes = self._cipher_suite.decrypt(value.encode())
                return decrypted_bytes.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt value for key '{key}': {e}")
                raise ValueError(f"Invalid encrypted value for key '{key}'")
        
        return value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return DatabaseConfig(
            url=self.get_secure_value('DATABASE_URL'),
            sqlite_path=os.getenv('SQLITE_DB_PATH'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30'))
        )
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return APIConfig(
            alpha_vantage_key=self.get_secure_value('ALPHA_VANTAGE_API_KEY'),
            twelvedata_key=self.get_secure_value('TWELVEDATA_API_KEY'),
            polygon_key=self.get_secure_value('POLYGON_API_KEY'),
            finnhub_key=self.get_secure_value('FINNHUB_API_KEY'),
            newsapi_key=self.get_secure_value('NEWSAPI_KEY'),
            youtube_key=self.get_secure_value('YOUTUBE_API_KEY'),
            claude_key=self.get_secure_value('CLAUDE_API_KEY')
        )
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return SecurityConfig(
            secret_key=self.get_secure_value('SECRET_KEY'),
            encryption_key=self.get_secure_value('ENCRYPTION_KEY'),
            jwt_secret=self.get_secure_value('JWT_SECRET_KEY'),
            enable_https=os.getenv('ENABLE_HTTPS', 'false').lower() == 'true',
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600'))
        )
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limiting configuration"""
        return RateLimitConfig(
            per_minute=int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '60')),
            per_hour=int(os.getenv('API_RATE_LIMIT_PER_HOUR', '1000')),
            per_day=int(os.getenv('API_RATE_LIMIT_PER_DAY', '10000'))
        )
    
    def get_portfolio_config(self) -> Dict[str, Any]:
        """Get portfolio configuration"""
        return {
            'default_balance': float(os.getenv('DEFAULT_PORTFOLIO_BALANCE', '900.00')),
            'default_risk_tolerance': os.getenv('DEFAULT_RISK_TOLERANCE', 'medium'),
            'max_position_percent': float(os.getenv('DEFAULT_MAX_POSITION_PERCENT', '15.0')),
            'rebalance_threshold': float(os.getenv('REBALANCE_THRESHOLD', '5.0')),
            'min_position_size': float(os.getenv('MIN_POSITION_SIZE', '50.00'))
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
        return os.getenv('LOG_LEVEL', 'INFO').upper()


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