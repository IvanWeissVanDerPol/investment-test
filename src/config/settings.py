"""
Centralized application settings using Pydantic BaseSettings.

Loads configuration from environment variables and optional .env files.
Use get_settings() to access a cached singleton across the app.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, BaseSettings, validator, Field
from typing import List


class DatabaseSettings(BaseModel):
    database_url: str
    sqlite_db_path: Optional[str] = None
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30


class APISettings(BaseModel):
    alpha_vantage_api_key: Optional[str] = None
    twelvedata_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None


class SecuritySettings(BaseModel):
    secret_key: str
    encryption_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    enable_https: bool = False
    session_timeout: int = 3600
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    @validator('jwt_secret_key')
    def jwt_secret_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters')
        return v
    
    @validator('secret_key')
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters')
        return v


class RateLimitSettings(BaseModel):
    api_rate_limit_per_minute: int = 60
    api_rate_limit_per_hour: int = 1000
    api_rate_limit_per_day: int = 10000


class PortfolioSettings(BaseModel):
    default_portfolio_balance: float = 900.0
    default_risk_tolerance: str = "medium"
    default_max_position_percent: float = 15.0
    rebalance_threshold: float = 5.0
    min_position_size: float = 50.0


class RedisSettings(BaseModel):
    redis_url: str = "redis://localhost:6379/1"


class IBSettings(BaseModel):
    ib_host: str = "127.0.0.1"
    ib_tws_port: int = 7497
    ib_gateway_port: int = 4001
    ib_client_id: int = 1


class EmailSettings(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_recipient: Optional[str] = None


class PowerBISettings(BaseModel):
    powerbi_report_id: Optional[str] = None


class CORSSettings(BaseModel):
    allow_origins: List[str] = ["http://localhost:3000"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    allow_headers: List[str] = ["*"]
    
    @validator('allow_origins')
    def validate_cors_origins(cls, v):
        if "*" in v and len(v) > 1:
            raise ValueError("Cannot use '*' with specific origins")
        return v


class MonitoringSettings(BaseModel):
    metrics_history_size: int = 10000
    enable_metrics: bool = True
    enable_health_checks: bool = True
    health_check_timeout: int = 5
    log_format: str = "json"
    

class AppSettings(BaseSettings):
    # Core App Configuration
    app_name: str = "Investment System API"
    api_version: str = "1.0.0"
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = False
    log_level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    
    # Server Configuration
    allowed_hosts: List[str] = ["*"]
    trusted_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # External URLs
    database_url: str = Field(..., description="Database connection URL")
    redis_url: Optional[str] = None

    # Nested Configuration Groups
    apis: APISettings = APISettings()
    security: SecuritySettings
    cors: CORSSettings = CORSSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    rate_limits: RateLimitSettings = RateLimitSettings()
    portfolio: PortfolioSettings = PortfolioSettings()
    ib: IBSettings = IBSettings()
    email: EmailSettings = EmailSettings()
    powerbi: PowerBISettings = PowerBISettings()
    
    # Validation
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v
    
    @validator('allowed_hosts')
    def validate_allowed_hosts(cls, v, values):
        if values.get('environment') == 'production' and '*' in v:
            raise ValueError('Wildcard hosts not allowed in production')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v or not v.startswith(('sqlite:///', 'postgresql://', 'mysql://', 'sqlite+aiosqlite://')):
            raise ValueError('Invalid database URL format')
        return v

    class Config:
        env_file = [".env.local", ".env"]
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True
        allow_population_by_field_name = True
        use_enum_values = True
        
        # Environment variable prefixes
        env_nested_delimiter = "__"
        
        # Field aliases for environment variables
        fields = {
            "app_name": {"env": "APP_NAME"},
            "api_version": {"env": "API_VERSION"},
            "environment": {"env": "ENVIRONMENT"},
            "debug": {"env": "DEBUG"},
            "log_level": {"env": "LOG_LEVEL"},
            "host": {"env": "HOST"},
            "port": {"env": "PORT"},
            "database_url": {"env": "DATABASE_URL"},
            "redis_url": {"env": "REDIS_URL"},
            "allowed_hosts": {"env": "ALLOWED_HOSTS"},
            "trusted_hosts": {"env": "TRUSTED_HOSTS"},
        }

    @classmethod
    def from_env(cls) -> "AppSettings":
        """Construct from environment variables using enhanced pydantic settings."""
        return cls(
            # Core app settings loaded automatically via BaseSettings
            # Nested models with proper validation
            security=SecuritySettings(
                secret_key=cls._get_str("SECRET_KEY", required=True),
                encryption_key=cls._get_str("ENCRYPTION_KEY", required=True), 
                jwt_secret_key=cls._get_str("JWT_SECRET_KEY", required=True),
                jwt_algorithm=cls._get_str("JWT_ALGORITHM", default="HS256"),
                jwt_access_token_expire_minutes=cls._get_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30),
                jwt_refresh_token_expire_days=cls._get_int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7),
                enable_https=cls._get_bool("ENABLE_HTTPS", False),
                session_timeout=cls._get_int("SESSION_TIMEOUT", 3600),
                password_min_length=cls._get_int("PASSWORD_MIN_LENGTH", 8),
                password_require_uppercase=cls._get_bool("PASSWORD_REQUIRE_UPPERCASE", True),
                password_require_numbers=cls._get_bool("PASSWORD_REQUIRE_NUMBERS", True),
                password_require_special=cls._get_bool("PASSWORD_REQUIRE_SPECIAL", True),
            ),
            cors=CORSSettings(
                allow_origins=cls._get_list("CORS_ALLOW_ORIGINS", ["http://localhost:3000"]),
                allow_credentials=cls._get_bool("CORS_ALLOW_CREDENTIALS", True),
                allow_methods=cls._get_list("CORS_ALLOW_METHODS", ["GET", "POST", "PUT", "DELETE"]),
                allow_headers=cls._get_list("CORS_ALLOW_HEADERS", ["*"]),
            ),
            monitoring=MonitoringSettings(
                metrics_history_size=cls._get_int("METRICS_HISTORY_SIZE", 10000),
                enable_metrics=cls._get_bool("ENABLE_METRICS", True),
                enable_health_checks=cls._get_bool("ENABLE_HEALTH_CHECKS", True),
                health_check_timeout=cls._get_int("HEALTH_CHECK_TIMEOUT", 5),
                log_format=cls._get_str("LOG_FORMAT", default="json"),
            ),
            # Other nested models with improved validation
            apis=APISettings(
                alpha_vantage_api_key=cls._get_optional_str("ALPHA_VANTAGE_API_KEY"),
                twelvedata_api_key=cls._get_optional_str("TWELVEDATA_API_KEY"),
                polygon_api_key=cls._get_optional_str("POLYGON_API_KEY"),
                finnhub_api_key=cls._get_optional_str("FINNHUB_API_KEY"),
                newsapi_key=cls._get_optional_str("NEWSAPI_KEY"),
                youtube_api_key=cls._get_optional_str("YOUTUBE_API_KEY"),
                claude_api_key=cls._get_optional_str("CLAUDE_API_KEY"),
                alpaca_api_key=cls._get_optional_str("ALPACA_API_KEY"),
                alpaca_api_secret=cls._get_optional_str("ALPACA_API_SECRET"),
            ),
            rate_limits=RateLimitSettings(
                api_rate_limit_per_minute=cls._get_int("API_RATE_LIMIT_PER_MINUTE", 60),
                api_rate_limit_per_hour=cls._get_int("API_RATE_LIMIT_PER_HOUR", 1000),
                api_rate_limit_per_day=cls._get_int("API_RATE_LIMIT_PER_DAY", 10000),
            ),
            portfolio=PortfolioSettings(
                default_portfolio_balance=cls._get_float("DEFAULT_PORTFOLIO_BALANCE", 900.0),
                default_risk_tolerance=cls._get_str("DEFAULT_RISK_TOLERANCE", default="medium"),
                default_max_position_percent=cls._get_float("DEFAULT_MAX_POSITION_PERCENT", 15.0),
                rebalance_threshold=cls._get_float("REBALANCE_THRESHOLD", 5.0),
                min_position_size=cls._get_float("MIN_POSITION_SIZE", 50.0),
            ),
            ib=IBSettings(
                ib_host=cls._get_str("IB_HOST", default="127.0.0.1"),
                ib_tws_port=cls._get_int("IB_TWS_PORT", 7497),
                ib_gateway_port=cls._get_int("IB_GATEWAY_PORT", 4001),
                ib_client_id=cls._get_int("IB_CLIENT_ID", 1),
            ),
            email=EmailSettings(
                smtp_server=cls._get_optional_str("SMTP_SERVER"),
                smtp_port=cls._get_int("SMTP_PORT", 587),
                smtp_username=cls._get_optional_str("SMTP_USERNAME"),
                smtp_password=cls._get_optional_str("SMTP_PASSWORD"),
                email_recipient=cls._get_optional_str("EMAIL_RECIPIENT"),
            ),
            powerbi=PowerBISettings(powerbi_report_id=cls._get_optional_str("POWERBI_REPORT_ID")),
        )

    # Enhanced helper getters with validation
    @staticmethod
    def _get_str(name: str, required: bool = True, default: Optional[str] = None) -> str:
        import os

        val = os.getenv(name, default)
        if required and (val is None or val == ""):
            raise ValueError(f"Missing required environment variable: {name}")
        return val if val is not None else ""

    @staticmethod
    def _get_optional_str(name: str) -> Optional[str]:
        import os
        
        val = os.getenv(name)
        return val if val and val.strip() else None

    @staticmethod
    def _get_int(name: str, default: int) -> int:
        import os

        try:
            val = os.getenv(name)
            if val is None:
                return default
            return int(val)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid integer value for {name}: {os.getenv(name)}. Error: {e}")

    @staticmethod
    def _get_float(name: str, default: float) -> float:
        import os

        try:
            val = os.getenv(name)
            if val is None:
                return default
            return float(val)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid float value for {name}: {os.getenv(name)}. Error: {e}")

    @staticmethod
    def _get_bool(name: str, default: bool) -> bool:
        import os

        val = os.getenv(name)
        if val is None:
            return default
        return val.lower() in {"1", "true", "yes", "on"}
    
    @staticmethod
    def _get_list(name: str, default: List[str]) -> List[str]:
        import os
        
        val = os.getenv(name)
        if val is None:
            return default
        # Support comma-separated values
        return [item.strip() for item in val.split(",") if item.strip()]
    
    # Properties for commonly accessed configuration
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins list."""
        return self.cors.allow_origins
    
    @property
    def cors_allow_credentials(self) -> bool:
        """Get CORS allow credentials setting."""
        return self.cors.allow_credentials
    
    @property
    def cors_allow_methods(self) -> List[str]:
        """Get CORS allowed methods."""
        return self.cors.allow_methods
    
    @property
    def cors_allow_headers(self) -> List[str]:
        """Get CORS allowed headers."""
        return self.cors.allow_headers
    
    @property
    def log_format(self) -> str:
        """Get logging format."""
        return self.monitoring.log_format
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached settings instance built from environment variables."""
    return AppSettings.from_env()
