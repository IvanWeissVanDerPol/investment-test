"""
Service layer initialization.
Provides business logic layer interfaces and implementations.
"""

from .base import (
    BaseService, CRUDService, ServiceResult, PaginatedResult,
    ValidationMixin, AuthorizationMixin, CacheableMixin
)
from .user_service import UserService

# Keep existing signal_service as is for now to avoid breaking changes
# from .signal_service import SignalService

__all__ = [
    # Base classes
    "BaseService",
    "CRUDService",
    "ServiceResult",
    "PaginatedResult",
    
    # Mixins
    "ValidationMixin",
    "AuthorizationMixin", 
    "CacheableMixin",
    
    # Concrete services
    "UserService",
    # "SignalService",  # Keep existing implementation for now
]