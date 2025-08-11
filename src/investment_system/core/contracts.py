"""
Core contracts for the investment system.
All data models and interfaces are defined here.
This ensures type safety and clear boundaries between modules.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


# Enums
class UserTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class IndicatorType(str, Enum):
    """Technical indicator types"""
    RSI = "rsi"
    SMA_20 = "sma_20"
    SMA_50 = "sma_50"
    MACD = "macd"
    VOLUME = "volume"
    BOLLINGER = "bollinger"


# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamp"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# Market Data Models
class PricePoint(BaseModel):
    """Single price point"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    
    @validator('open', 'high', 'low', 'close')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v


class MarketData(TimestampedModel):
    """Market data for a symbol"""
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    prices: List[PricePoint]
    is_stale: bool = False
    source: str = "yfinance"
    
    @property
    def latest_price(self) -> Optional[Decimal]:
        """Get the most recent price"""
        if self.prices:
            return self.prices[-1].close
        return None
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "prices": [{"timestamp": "2025-08-09T10:00:00", "open": 150.0, "high": 152.0, "low": 149.0, "close": 151.0, "volume": 1000000}],
                "is_stale": False
            }
        }


# Signal Models
class Indicator(BaseModel):
    """Technical indicator value"""
    type: IndicatorType
    value: float
    timestamp: datetime


class TradingSignal(TimestampedModel):
    """Trading signal with indicators"""
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    signal: SignalType
    confidence: float = Field(..., ge=0, le=1)
    price: Decimal
    indicators: Dict[IndicatorType, float]
    reasoning: Optional[str] = None
    ai_enhanced: bool = False
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 4)
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "signal": "buy",
                "confidence": 0.85,
                "price": 151.0,
                "indicators": {"rsi": 45, "sma_20": 150, "sma_50": 148}
            }
        }


# User Models
class User(TimestampedModel):
    """User model"""
    id: str
    email: str
    tier: UserTier = UserTier.FREE
    stripe_customer_id: Optional[str] = None
    api_key: str
    is_active: bool = True
    
    @property
    def tier_limits(self) -> Dict[str, Any]:
        """Get tier-specific limits"""
        limits = {
            UserTier.FREE: {"api_calls": 100, "symbols": 5, "signals_per_day": 10},
            UserTier.STARTER: {"api_calls": 1000, "symbols": 20, "signals_per_day": 100},
            UserTier.PRO: {"api_calls": 10000, "symbols": 100, "signals_per_day": 1000},
            UserTier.ENTERPRISE: {"api_calls": -1, "symbols": -1, "signals_per_day": -1}
        }
        return limits.get(self.tier, limits[UserTier.FREE])


class Subscription(TimestampedModel):
    """Subscription model"""
    user_id: str
    tier: UserTier
    stripe_subscription_id: str
    status: str = "active"
    current_period_end: datetime
    cancel_at_period_end: bool = False


# API Models
class APIUsage(TimestampedModel):
    """API usage tracking"""
    user_id: str
    endpoint: str
    method: str
    units: int = 1
    response_time_ms: Optional[int] = None
    status_code: int
    ip_address: Optional[str] = None


class RateLimitStatus(BaseModel):
    """Rate limit status"""
    limit: int
    remaining: int
    reset_at: datetime
    tier: UserTier


# Request/Response Models
class SignalRequest(BaseModel):
    """Request for signal generation"""
    symbols: List[str] = Field(..., min_items=1, max_items=100)
    lookback_days: int = Field(120, ge=1, le=365)
    indicators: Optional[List[IndicatorType]] = None
    
    @validator('symbols')
    def validate_symbols(cls, v):
        for symbol in v:
            if not symbol.isupper() or len(symbol) > 5:
                raise ValueError(f'Invalid symbol: {symbol}')
        return v


class SignalResponse(BaseModel):
    """Response with signals"""
    signals: List[TradingSignal]
    request_id: str
    cached: bool = False
    rate_limit: RateLimitStatus


class MarketDataRequest(BaseModel):
    """Request for market data"""
    symbols: List[str] = Field(..., min_items=1, max_items=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('symbols')
    def validate_symbols(cls, v):
        for symbol in v:
            if not symbol.isupper() or len(symbol) > 5:
                raise ValueError(f'Invalid symbol: {symbol}')
        return v


class MarketDataResponse(BaseModel):
    """Response with market data"""
    data: List[MarketData]
    request_id: str
    cached: bool = False
    rate_limit: RateLimitStatus


# Error Models
class ErrorCode(str, Enum):
    """Standard error codes"""
    INVALID_SYMBOL = "E001"
    DATA_FETCH_FAILED = "E002"
    ANALYSIS_FAILED = "E003"
    RATE_LIMIT_EXCEEDED = "E004"
    SUBSCRIPTION_REQUIRED = "E005"
    AUTHENTICATION_FAILED = "E006"
    INVALID_REQUEST = "E007"
    INTERNAL_ERROR = "E999"


class ErrorResponse(BaseModel):
    """Standard error response"""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "E004",
                "message": "Rate limit exceeded",
                "details": {"limit": 100, "reset_at": "2025-08-09T12:00:00"}
            }
        }


# Billing Models
class UsageStats(BaseModel):
    """User usage statistics"""
    user_id: str
    period_start: datetime
    period_end: datetime
    api_calls: int
    unique_symbols: int
    signals_generated: int
    data_points_fetched: int
    
    def calculate_overage(self, tier: UserTier) -> Dict[str, int]:
        """Calculate overage charges"""
        limits = User(id="", email="", tier=tier, api_key="").tier_limits
        overage = {}
        
        if limits["api_calls"] != -1 and self.api_calls > limits["api_calls"]:
            overage["api_calls"] = self.api_calls - limits["api_calls"]
            
        if limits["symbols"] != -1 and self.unique_symbols > limits["symbols"]:
            overage["symbols"] = self.unique_symbols - limits["symbols"]
            
        return overage


# AI Hook Models
class AIHookRequest(BaseModel):
    """Request for AI hook processing"""
    hook_id: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class AIHookResponse(BaseModel):
    """Response from AI hook"""
    hook_id: str
    processed_data: Dict[str, Any]
    modifications_made: bool
    confidence: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = None