"""
API module with centralized endpoint management.
Single source of truth for all API routes.
"""

from .router import EndpointCatalog, DynamicRouter, create_dynamic_router, get_endpoint_url
from .deps import (
    get_auth_dependency,
    get_rate_limiter_dependency,
    get_tier_dependency,
    idempotency_dependency,
    verify_token,
    verify_admin_token,
    verify_api_key
)

__all__ = [
    "EndpointCatalog",
    "DynamicRouter", 
    "create_dynamic_router",
    "get_endpoint_url",
    "get_auth_dependency",
    "get_rate_limiter_dependency",
    "get_tier_dependency",
    "idempotency_dependency",
    "verify_token",
    "verify_admin_token",
    "verify_api_key"
]