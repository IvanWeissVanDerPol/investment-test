"""
Centralized application settings using Pydantic BaseSettings.

Loads configuration from environment variables and optional .env files.
Use get_settings() to access a cached singleton across the app.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel
from pydantic.env_settings import BaseSettings


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
    enable_https: bool = False
    session_timeout: int = 3600


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


class AppSettings(BaseSettings):
    # App
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Nested groups
    database: DatabaseSettings
    apis: APISettings
    security: SecuritySettings
    rate_limits: RateLimitSettings = RateLimitSettings()
    portfolio: PortfolioSettings = PortfolioSettings()
    redis: RedisSettings = RedisSettings()
    ib: IBSettings = IBSettings()
    email: EmailSettings = EmailSettings()
    powerbi: PowerBISettings = PowerBISettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Mapping environment variable names to nested fields
        fields = {
            # Database
            "database": {
                "env": [
                    "DATABASE_URL",
                    "SQLITE_DB_PATH",
                    "DB_POOL_SIZE",
                    "DB_MAX_OVERFLOW",
                    "DB_POOL_TIMEOUT",
                ]
            },
            # APIs
            "apis": {
                "env": [
                    "ALPHA_VANTAGE_API_KEY",
                    "TWELVEDATA_API_KEY",
                    "POLYGON_API_KEY",
                    "FINNHUB_API_KEY",
                    "NEWSAPI_KEY",
                    "YOUTUBE_API_KEY",
                    "CLAUDE_API_KEY",
                    "ALPACA_API_KEY",
                    "ALPACA_API_SECRET",
                ]
            },
            # Security
            "security": {
                "env": [
                    "SECRET_KEY",
                    "ENCRYPTION_KEY",
                    "JWT_SECRET_KEY",
                    "ENABLE_HTTPS",
                    "SESSION_TIMEOUT",
                ]
            },
            # Rate limits
            "rate_limits": {
                "env": [
                    "API_RATE_LIMIT_PER_MINUTE",
                    "API_RATE_LIMIT_PER_HOUR",
                    "API_RATE_LIMIT_PER_DAY",
                ]
            },
            # Portfolio
            "portfolio": {
                "env": [
                    "DEFAULT_PORTFOLIO_BALANCE",
                    "DEFAULT_RISK_TOLERANCE",
                    "DEFAULT_MAX_POSITION_PERCENT",
                    "REBALANCE_THRESHOLD",
                    "MIN_POSITION_SIZE",
                ]
            },
            # Redis
            "redis": {"env": ["REDIS_URL"]},
            # IB
            "ib": {
                "env": ["IB_HOST", "IB_TWS_PORT", "IB_GATEWAY_PORT", "IB_CLIENT_ID"]
            },
            # Email
            "email": {
                "env": [
                    "SMTP_SERVER",
                    "SMTP_PORT",
                    "SMTP_USERNAME",
                    "SMTP_PASSWORD",
                    "EMAIL_RECIPIENT",
                ]
            },
            # PowerBI
            "powerbi": {"env": ["POWERBI_REPORT_ID"]},
        }

    @classmethod
    def from_env(cls) -> "AppSettings":
        """Construct from environment variables using pydantic settings."""
        # We need to manually construct nested models because BaseSettings does not
        # automatically create nested models from unrelated env vars.
        return cls(
            database=DatabaseSettings(
                database_url=cls._get_str("DATABASE_URL", required=True),
                sqlite_db_path=cls._get_optional_str("SQLITE_DB_PATH"),
                db_pool_size=cls._get_int("DB_POOL_SIZE", 10),
                db_max_overflow=cls._get_int("DB_MAX_OVERFLOW", 20),
                db_pool_timeout=cls._get_int("DB_POOL_TIMEOUT", 30),
            ),
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
            security=SecuritySettings(
                secret_key=cls._get_str("SECRET_KEY", required=True),
                encryption_key=cls._get_str("ENCRYPTION_KEY", required=True),
                jwt_secret_key=cls._get_str("JWT_SECRET_KEY", required=True),
                enable_https=cls._get_bool("ENABLE_HTTPS", False),
                session_timeout=cls._get_int("SESSION_TIMEOUT", 3600),
            ),
            rate_limits=RateLimitSettings(
                api_rate_limit_per_minute=cls._get_int("API_RATE_LIMIT_PER_MINUTE", 60),
                api_rate_limit_per_hour=cls._get_int("API_RATE_LIMIT_PER_HOUR", 1000),
                api_rate_limit_per_day=cls._get_int("API_RATE_LIMIT_PER_DAY", 10000),
            ),
            portfolio=PortfolioSettings(
                default_portfolio_balance=cls._get_float("DEFAULT_PORTFOLIO_BALANCE", 900.0),
                default_risk_tolerance=cls._get_str("DEFAULT_RISK_TOLERANCE", required=False, default="medium"),
                default_max_position_percent=cls._get_float("DEFAULT_MAX_POSITION_PERCENT", 15.0),
                rebalance_threshold=cls._get_float("REBALANCE_THRESHOLD", 5.0),
                min_position_size=cls._get_float("MIN_POSITION_SIZE", 50.0),
            ),
            redis=RedisSettings(redis_url=cls._get_str("REDIS_URL", required=False, default="redis://localhost:6379/1")),
            ib=IBSettings(
                ib_host=cls._get_str("IB_HOST", required=False, default="127.0.0.1"),
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
            environment=cls._get_str("ENVIRONMENT", required=False, default="development"),
            debug=cls._get_bool("DEBUG", False),
            log_level=cls._get_str("LOG_LEVEL", required=False, default="INFO"),
            host=cls._get_str("HOST", required=False, default="0.0.0.0"),
            port=cls._get_int("PORT", 8000),
        )

    # Helper getters
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

        return os.getenv(name)

    @staticmethod
    def _get_int(name: str, default: int) -> int:
        import os

        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            return default

    @staticmethod
    def _get_float(name: str, default: float) -> float:
        import os

        try:
            return float(os.getenv(name, str(default)))
        except ValueError:
            return default

    @staticmethod
    def _get_bool(name: str, default: bool) -> bool:
        import os

        return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached settings instance built from environment variables."""
    return AppSettings.from_env()
