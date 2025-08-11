"""
Middleware for automatic usage tracking and billing enforcement.
"""

import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from investment_system.services.usage_tracking import get_usage_tracker
from investment_system.core.contracts import UserTier

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically tracks API usage for billing.
    Also enforces usage limits based on user tiers.
    """
    
    def __init__(self, app, tracked_endpoints: Dict[str, int] = None):
        """
        Initialize usage tracking middleware.
        
        Args:
            app: FastAPI application
            tracked_endpoints: Dict mapping endpoints to cost units
        """
        super().__init__(app)
        self.usage_tracker = get_usage_tracker()
        
        # Define which endpoints cost units and how much
        self.tracked_endpoints = tracked_endpoints or {
            "/signals": 1,                    # 1 unit per signal request
            "/signals/history": 2,           # 2 units per history request
            "/export/csv": 3,                # 3 units per export
            "/export/pdf": 5,                # 5 units per PDF export
            "/billing/subscribe": 0,         # No usage cost
            "/billing/status": 0,            # No usage cost
            "/health": 0,                    # No usage cost
            "/webhooks": 0,                  # No usage cost
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with usage tracking."""
        start_time = time.time()
        
        # Extract path and check if it should be tracked
        path = request.url.path
        method = request.method
        
        # Skip tracking for non-tracked endpoints
        cost_units = self._get_endpoint_cost(path, method)
        user_id = await self._extract_user_id(request)
        
        # Check usage limits before processing request
        if cost_units > 0 and user_id:
            try:
                limit_check = await self.usage_tracker.check_usage_limits(user_id)
                if not limit_check["allowed"]:
                    logger.warning(f"Usage limit exceeded for user {user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={
                            "error": "usage_limit_exceeded",
                            "message": "Your usage limit has been reached. Please upgrade your plan.",
                            "current_usage": limit_check["current_usage"],
                            "limit": limit_check["included_units"]
                        }
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to check usage limits: {e}")
                # Continue processing - don't block requests due to usage tracking issues
        
        # Process the request
        try:
            response = await call_next(request)
            success = 200 <= response.status_code < 400
        except Exception as e:
            success = False
            response = Response(status_code=500)
            logger.error(f"Request failed: {e}")
        
        # Record usage after successful request
        if cost_units > 0 and user_id and success:
            try:
                processing_time = time.time() - start_time
                await self.usage_tracker.record_usage(
                    user_id=user_id,
                    endpoint=path,
                    method=method,
                    cost_units=cost_units,
                    metadata={
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "status_code": response.status_code,
                        "user_agent": request.headers.get("user-agent", ""),
                        "timestamp": time.time()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to record usage: {e}")
                # Don't fail the response due to usage tracking issues
        
        return response
    
    def _get_endpoint_cost(self, path: str, method: str) -> int:
        """
        Get cost units for an endpoint.
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            Number of cost units
        """
        # Direct match
        if path in self.tracked_endpoints:
            return self.tracked_endpoints[path]
        
        # Pattern matching for parameterized endpoints
        for tracked_path, cost in self.tracked_endpoints.items():
            if self._path_matches(path, tracked_path):
                return cost
        
        # Default: no cost for untracked endpoints
        return 0
    
    def _path_matches(self, actual_path: str, pattern: str) -> bool:
        """
        Check if actual path matches pattern.
        
        Args:
            actual_path: Actual request path
            pattern: Pattern to match against
            
        Returns:
            True if path matches pattern
        """
        # Handle parameterized paths like /signals/history/{symbol}
        actual_parts = actual_path.strip("/").split("/")
        pattern_parts = pattern.strip("/").split("/")
        
        if len(actual_parts) != len(pattern_parts):
            return False
        
        for actual, pattern_part in zip(actual_parts, pattern_parts):
            # Skip parameter placeholders
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue
            if actual != pattern_part:
                return False
        
        return True
    
    async def _extract_user_id(self, request: Request) -> str:
        """
        Extract user ID from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            User ID or None
        """
        try:
            # Check if user is in request state (added by auth middleware)
            if hasattr(request.state, "user_id"):
                return request.state.user_id
            
            # Try to extract from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Import here to avoid circular imports
            import jwt
            import os
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(
                token,
                os.getenv("JWT_SECRET"),
                algorithms=[os.getenv("JWT_ALGORITHM", "HS256")]
            )
            
            return payload.get("sub")
            
        except Exception as e:
            logger.debug(f"Could not extract user ID: {e}")
            return None


def create_usage_middleware(tracked_endpoints: Dict[str, int] = None):
    """
    Create usage tracking middleware with custom endpoint costs.
    
    Args:
        tracked_endpoints: Dict mapping endpoints to cost units
        
    Returns:
        Middleware class
    """
    class ConfiguredUsageMiddleware(UsageTrackingMiddleware):
        def __init__(self, app):
            super().__init__(app, tracked_endpoints)
    
    return ConfiguredUsageMiddleware