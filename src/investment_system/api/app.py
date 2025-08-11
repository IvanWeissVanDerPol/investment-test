"""
FastAPI application with authentication, rate limiting, and billing.
This is the main entry point for the revenue-generating API.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import secrets

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import jwt
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from investment_system.core.contracts import (
    User, UserTier, SignalRequest, SignalResponse,
    MarketDataRequest, MarketDataResponse,
    ErrorCode, ErrorResponse, RateLimitStatus
)
from investment_system.services.signal_service import get_signal_service
import io
import csv
import yaml

# Load dependency graph for AI agents
with open("config/dependency_graph.yaml", "r") as f:
    DEPENDENCY_GRAPH = yaml.safe_load(f)

# Initialize FastAPI app
app = FastAPI(
    title="Investment System API",
    description="AI-ready trading signals API with tiered subscriptions",
    version=DEPENDENCY_GRAPH["version"],
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()

# Mock database (replace with real DB in production)
USERS_DB = {}
SUBSCRIPTIONS_DB = {}

# JWT settings from environment
import os
from dotenv import load_dotenv
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", None)
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


# Pydantic models for auth
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tier: UserTier = UserTier.FREE


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SubscribeRequest(BaseModel):
    tier: UserTier
    payment_method_id: Optional[str] = None  # Stripe payment method


# Authentication functions
def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user_id"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(user_id: str = Depends(verify_token)) -> User:
    """Get current user from token"""
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_tier_rate_limit(tier: UserTier) -> str:
    """Get rate limit string for tier"""
    limits = {
        UserTier.FREE: "100/hour",
        UserTier.STARTER: "1000/hour",
        UserTier.PRO: "10000/hour",
        UserTier.ENTERPRISE: "100000/hour"
    }
    return limits.get(tier, "100/hour")


# Import routers
from investment_system.api.handlers import health_router
from investment_system.api.webhooks import webhook_router
from investment_system.api.handlers.billing import get_billing_handler

# Include routers
app.include_router(health_router)
app.include_router(webhook_router)

# Legacy health check endpoint (kept for compatibility)
@app.get("/healthz")
@limiter.limit("1000/minute")
async def health_check(request: Request):
    """Legacy health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": DEPENDENCY_GRAPH["version"],
        "dependency_graph": "loaded"
    }


# Authentication endpoints
@app.post("/auth/register")
@limiter.limit("10/hour")
async def register(request: Request, register_req: RegisterRequest):
    """Register a new user"""
    # Check if email exists
    if any(u.email == register_req.email for u in USERS_DB.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)
    
    user = User(
        id=user_id,
        email=register_req.email,
        tier=register_req.tier,
        api_key=api_key
    )
    
    USERS_DB[user_id] = user
    
    # Create access token
    access_token = create_access_token(user_id)
    
    return {
        "user_id": user_id,
        "email": user.email,
        "tier": user.tier,
        "api_key": api_key,
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/auth/login")
@limiter.limit("20/hour")
async def login(request: Request, login_req: LoginRequest):
    """Login user"""
    # Find user by email
    user = None
    for u in USERS_DB.values():
        if u.email == login_req.email:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(user.id)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "tier": user.tier,
        "access_token": access_token,
        "token_type": "bearer"
    }


# Billing endpoints
from investment_system.api.handlers.billing import (
    get_billing_handler,
    CreateSubscriptionRequest,
    UpgradeSubscriptionRequest,
    CancelSubscriptionRequest
)

@app.post("/billing/subscribe")
@limiter.limit("5/hour")
async def create_subscription(
    request: Request,
    subscribe_req: CreateSubscriptionRequest,
    user: User = Depends(get_current_user)
):
    """Create new subscription with Stripe integration"""
    billing_handler = get_billing_handler()
    return await billing_handler.create_subscription(subscribe_req, user)


@app.get("/billing/status")
@limiter.limit("100/hour")
async def get_billing_status(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Get subscription status and billing information"""
    billing_handler = get_billing_handler()
    return await billing_handler.get_subscription_status(user)


@app.post("/billing/upgrade")
@limiter.limit("5/hour")
async def upgrade_subscription(
    request: Request,
    upgrade_req: UpgradeSubscriptionRequest,
    user: User = Depends(get_current_user)
):
    """Upgrade subscription tier"""
    billing_handler = get_billing_handler()
    return await billing_handler.upgrade_subscription(upgrade_req, user)


@app.post("/billing/cancel")
@limiter.limit("3/hour")
async def cancel_subscription(
    request: Request,
    cancel_req: CancelSubscriptionRequest,
    user: User = Depends(get_current_user)
):
    """Cancel subscription"""
    billing_handler = get_billing_handler()
    return await billing_handler.cancel_subscription(cancel_req, user)


@app.get("/billing/payment-methods")
@limiter.limit("20/hour")
async def get_payment_methods(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Get user's payment methods"""
    billing_handler = get_billing_handler()
    return await billing_handler.get_payment_methods(user)


@app.get("/billing/portal")
@limiter.limit("10/hour")
async def get_billing_portal(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Get Stripe billing portal URL"""
    billing_handler = get_billing_handler()
    return await billing_handler.get_billing_portal_url(user)


@app.get("/pricing")
@limiter.limit("1000/hour")
async def get_pricing(request: Request):
    """Get pricing information for all tiers"""
    billing_handler = get_billing_handler()
    return await billing_handler.get_pricing_info()


# Legacy subscription endpoint (kept for backwards compatibility)
@app.post("/subscribe")
@limiter.limit("5/hour")
async def legacy_subscribe(
    request: Request,
    subscribe_req: SubscribeRequest,
    user: User = Depends(get_current_user)
):
    """Legacy subscription endpoint - redirects to new billing system"""
    from investment_system.api.handlers.billing import CreateSubscriptionRequest
    
    if subscribe_req.tier == UserTier.FREE:
        # Handle downgrade
        billing_handler = get_billing_handler()
        cancel_req = CancelSubscriptionRequest(at_period_end=False, reason="downgrade_to_free")
        return await billing_handler.cancel_subscription(cancel_req, user)
    
    # Convert to new format
    create_req = CreateSubscriptionRequest(
        tier=subscribe_req.tier,
        payment_method_id=subscribe_req.payment_method_id or "pm_mock_test"
    )
    
    billing_handler = get_billing_handler()
    return await billing_handler.create_subscription(create_req, user)


# Trading signal endpoints
@app.post("/signals", response_model=SignalResponse)
async def get_signals(
    request: Request,
    signal_req: SignalRequest,
    user: User = Depends(get_current_user)
):
    """Generate trading signals (main revenue endpoint)"""
    # Apply tier-based rate limiting dynamically
    # This is a simplified version - in production use a proper rate limiter
    
    # Check user limits
    if user.tier == UserTier.FREE and len(signal_req.symbols) > 5:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Free tier limited to 5 symbols. You requested {len(signal_req.symbols)}"
        )
    
    # Get signal service
    signal_service = get_signal_service()
    
    try:
        # Generate signals
        response = await signal_service.generate_signals(signal_req, user)
        return response
    except ValueError as e:
        if str(e) == ErrorCode.SUBSCRIPTION_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Subscription required for this feature"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signals"
        )


@app.get("/signals/history/{symbol}")
async def get_signal_history(
    request: Request,
    symbol: str,
    days: int = 7,
    user: User = Depends(get_current_user)
):
    """Get historical signals for a symbol (premium feature)"""
    if user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Historical data requires a paid subscription"
        )
    
    signal_service = get_signal_service()
    
    try:
        history = await signal_service.get_signal_history(symbol, user, days)
        return {"symbol": symbol, "days": days, "signals": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch history"
        )


# Export endpoints
@app.get("/export/csv")
async def export_csv(
    request: Request,
    symbols: str,  # Comma-separated symbols
    user: User = Depends(get_current_user)
):
    """Export signals as CSV (premium feature)"""
    if user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="CSV export requires a paid subscription"
        )
    
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    # Generate signals
    signal_service = get_signal_service()
    signal_req = SignalRequest(symbols=symbol_list)
    
    try:
        response = await signal_service.generate_signals(signal_req, user)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["symbol", "signal", "confidence", "price", "rsi", "sma_20", "sma_50", "timestamp"]
        )
        writer.writeheader()
        
        for signal in response.signals:
            writer.writerow({
                "symbol": signal.symbol,
                "signal": signal.signal,
                "confidence": signal.confidence,
                "price": signal.price,
                "rsi": signal.indicators.get("rsi", ""),
                "sma_20": signal.indicators.get("sma_20", ""),
                "sma_50": signal.indicators.get("sma_50", ""),
                "timestamp": signal.created_at.isoformat()
            })
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export CSV"
        )


# Usage and billing endpoints
@app.get("/usage")
async def get_usage(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Get current usage statistics"""
    # In production, query from database
    # For MVP, return mock data
    limits = user.tier_limits
    
    return {
        "user_id": user.id,
        "tier": user.tier,
        "current_usage": {
            "api_calls": 42,
            "symbols_queried": 15,
            "signals_generated": 30
        },
        "limits": limits,
        "billing_period": {
            "start": datetime.utcnow().replace(day=1).isoformat(),
            "end": (datetime.utcnow().replace(day=1) + timedelta(days=31)).isoformat()
        }
    }


# AI Integration endpoints (for future use)
@app.get("/dependency-graph")
async def get_dependency_graph(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Get system dependency graph (for AI agents)"""
    if user.tier not in [UserTier.ENTERPRISE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dependency graph requires enterprise tier"
        )
    
    return DEPENDENCY_GRAPH


@app.post("/ai/hook")
async def register_ai_hook(
    request: Request,
    hook_name: str,
    user: User = Depends(get_current_user)
):
    """Register an AI hook (enterprise feature)"""
    if user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI hooks require enterprise tier"
        )
    
    # In production, this would register actual hooks
    return {
        "message": f"Hook {hook_name} registered",
        "available_hooks": [
            "pre_analysis",
            "post_indicators",
            "signal_override",
            "confidence_adjustment"
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard error response"""
    error_code = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.AUTHENTICATION_FAILED,
        402: ErrorCode.SUBSCRIPTION_REQUIRED,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR
    }.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=exc.detail,
            request_id=str(uuid.uuid4())
        ).dict()
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"Starting Investment System API v{DEPENDENCY_GRAPH['version']}")
    print(f"Dependency graph loaded with {len(DEPENDENCY_GRAPH['modules'])} modules")
    print("AI hooks ready for registration")
    
    # Create demo user only in development mode
    if os.getenv("ENVIRONMENT", "development") == "development":
        demo_api_key = os.getenv("DEMO_API_KEY", secrets.token_urlsafe(32))
        demo_user = User(
            id="demo-user-id",
            email="demo@example.com",
            tier=UserTier.PRO,
            api_key=demo_api_key
        )
        USERS_DB["demo-user-id"] = demo_user
        print("Demo user created for development: demo@example.com")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)