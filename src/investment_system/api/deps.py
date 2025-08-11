"""
API dependencies for authentication, rate limiting, and other middleware.
Used by the dynamic router to apply security and business logic.
"""

import hashlib
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from investment_system.core.contracts import UserTier, User
from investment_system.security.rate_limit import rate_limiter
from investment_system.infrastructure.database import get_db
from investment_system.infrastructure.crud import UserCRUD


# Security scheme
security = HTTPBearer()


def get_auth_dependency(auth_type: str) -> Callable:
    """
    Get authentication dependency based on type.
    
    Args:
        auth_type: Authentication type (none, jwt, jwt:admin, api_key, webhook_signature:provider)
        
    Returns:
        FastAPI dependency function
    """
    if auth_type == "none":
        return lambda: None
    elif auth_type == "jwt":
        return verify_token
    elif auth_type == "jwt:admin":
        return verify_admin_token
    elif auth_type == "api_key":
        return verify_api_key
    elif auth_type.startswith("webhook_signature:"):
        provider = auth_type.split(":")[1]
        return get_webhook_verifier(provider)
    else:
        raise ValueError(f"Unknown auth type: {auth_type}")


def get_rate_limiter_dependency(rate_spec: str, tier_limits: Optional[Dict] = None) -> Callable:
    """
    Get rate limiter dependency.
    
    Args:
        rate_spec: Rate specification (e.g., "100/h", "60/m", "dynamic")
        tier_limits: Optional tier-specific limits for dynamic rating
        
    Returns:
        FastAPI dependency function
    """
    if rate_spec == "dynamic":
        return create_dynamic_rate_limiter(tier_limits or {})
    
    # Parse rate spec (e.g., "100/h" -> 100 requests per hour)
    parts = rate_spec.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid rate spec: {rate_spec}")
    
    limit = int(parts[0])
    period = parts[1]
    
    # Convert period to seconds
    period_seconds = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }.get(period, 60)
    
    async def rate_limit_check(request: Request):
        """Check rate limit for request."""
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        
        # Use user ID if authenticated, otherwise IP
        key = f"user:{user_id}" if user_id else f"ip:{hashlib.md5(client_ip.encode()).hexdigest()}"
        
        # Check rate limit
        allowed, remaining, reset_time = rate_limiter.check_rate_limit(
            key=key,
            max_requests=limit,
            window_seconds=period_seconds
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again at {reset_time.isoformat()}"
            )
        
        # Add rate limit info to request state
        request.state.rate_limit = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time
        }
    
    return rate_limit_check


def get_tier_dependency(required_tier: str) -> Callable:
    """
    Get tier checking dependency.
    
    Args:
        required_tier: Required tier (all, paid, pro, enterprise, admin)
        
    Returns:
        FastAPI dependency function
    """
    async def check_tier(request: Request):
        """Check if user has required tier."""
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_tier = user.tier
        
        # Check tier requirements
        if required_tier == "all":
            return True
        elif required_tier == "paid":
            if user_tier == UserTier.FREE:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Paid subscription required"
                )
        elif required_tier == "pro":
            if user_tier not in [UserTier.PRO, UserTier.ENTERPRISE]:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Pro or Enterprise subscription required"
                )
        elif required_tier == "enterprise":
            if user_tier != UserTier.ENTERPRISE:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Enterprise subscription required"
                )
        elif required_tier == "admin":
            # Check admin flag (would be in user model)
            if not getattr(user, "is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
    
    return check_tier


def idempotency_dependency() -> Callable:
    """
    Get idempotency checking dependency for mutating operations.
    
    Returns:
        FastAPI dependency function
    """
    async def check_idempotency(request: Request):
        """Check idempotency key for request."""
        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")
        
        if not idempotency_key:
            # Idempotency is optional but recommended
            return
        
        # Check if we've seen this key before (would check cache/DB)
        # For now, just store in request state
        request.state.idempotency_key = idempotency_key
    
    return check_idempotency


async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Verify JWT token and return user.
    
    Args:
        request: FastAPI request
        credentials: Bearer token credentials
        
    Returns:
        Authenticated user
    """
    import os
    JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT configuration error"
        )
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        db = next(get_db())
        user = UserCRUD.get_user(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Store user in request state
        request.state.user_id = user_id
        request.state.user = user
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    finally:
        db.close()


async def verify_admin_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Verify JWT token and ensure user is admin.
    
    Args:
        request: FastAPI request
        credentials: Bearer token credentials
        
    Returns:
        Authenticated admin user
    """
    user = await verify_token(request, credentials)
    
    # Check if user is admin (would check user.is_admin field)
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


async def verify_api_key(request: Request) -> User:
    """
    Verify API key authentication.
    
    Args:
        request: FastAPI request
        
    Returns:
        Authenticated user
    """
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Parse API key (format: "key_id:secret_key")
    if ":" not in api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    key_id, secret_key = api_key.split(":", 1)
    
    # Verify API key
    db = next(get_db())
    try:
        user = UserCRUD.get_user_by_api_key(db, key_id, secret_key)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Store user in request state
        request.state.user_id = str(user.id)
        request.state.user = user
        
        return user
    finally:
        db.close()


def get_webhook_verifier(provider: str) -> Callable:
    """
    Get webhook signature verifier for provider.
    
    Args:
        provider: Webhook provider (stripe, github, etc.)
        
    Returns:
        Verification function
    """
    async def verify_webhook(request: Request):
        """Verify webhook signature."""
        if provider == "stripe":
            # Verify Stripe webhook signature
            import stripe
            import os
            
            webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
            if not webhook_secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Webhook configuration error"
                )
            
            # Get signature from header
            signature = request.headers.get("Stripe-Signature")
            if not signature:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing webhook signature"
                )
            
            # Get raw body
            body = await request.body()
            
            try:
                # Verify signature
                stripe.Webhook.construct_event(
                    body, signature, webhook_secret
                )
            except stripe.error.SignatureVerificationError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        else:
            raise ValueError(f"Unknown webhook provider: {provider}")
    
    return verify_webhook


def create_dynamic_rate_limiter(tier_limits: Dict[str, str]) -> Callable:
    """
    Create dynamic rate limiter based on user tier.
    
    Args:
        tier_limits: Tier-specific rate limits
        
    Returns:
        Rate limiting function
    """
    async def dynamic_rate_limit(request: Request):
        """Apply tier-based rate limiting."""
        user = getattr(request.state, "user", None)
        
        if not user:
            # Use free tier for unauthenticated
            rate_spec = tier_limits.get("free", "100/h")
        else:
            # Use user's tier
            tier_name = user.tier.value.lower()
            rate_spec = tier_limits.get(tier_name, "100/h")
        
        if rate_spec == "unlimited":
            return
        
        # Apply rate limit
        limiter = get_rate_limiter_dependency(rate_spec)
        await limiter(request)
    
    return dynamic_rate_limit