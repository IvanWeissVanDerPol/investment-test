"""
Base service layer abstractions for business logic separation.
Provides common patterns and interfaces for service implementations.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')


@dataclass
class ServiceResult:
    """
    Standard result container for service operations.
    Provides consistent response format across all services.
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(cls, data: Any = None, metadata: Optional[Dict[str, Any]] = None) -> 'ServiceResult':
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, error_code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'ServiceResult':
        """Create an error result."""
        return cls(success=False, error=error, error_code=error_code, metadata=metadata)


@dataclass
class PaginatedResult:
    """
    Container for paginated service results.
    """
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total_count + self.page_size - 1) // self.page_size


class BaseService(ABC, Generic[T]):
    """
    Abstract base service providing common business logic patterns.
    
    All services should inherit from this class to ensure consistent
    interface and error handling across the business logic layer.
    """
    
    def __init__(self):
        self._logger = None
    
    @property
    def logger(self):
        """Lazy logger initialization."""
        if self._logger is None:
            from investment_system.core.logging import get_logger
            self._logger = get_logger(self.__class__.__module__)
        return self._logger
    
    async def validate_input(self, data: Dict[str, Any]) -> ServiceResult:
        """
        Validate input data for service operations.
        
        Args:
            data: Input data to validate
            
        Returns:
            ServiceResult indicating validation success or failure
        """
        # Default implementation - override in subclasses
        return ServiceResult.success_result()
    
    async def authorize_operation(
        self, 
        user_id: str, 
        operation: str, 
        resource_id: Optional[str] = None
    ) -> ServiceResult:
        """
        Check if user is authorized to perform the operation.
        
        Args:
            user_id: User performing the operation
            operation: Operation being attempted
            resource_id: Optional resource identifier
            
        Returns:
            ServiceResult indicating authorization success or failure
        """
        # Default implementation allows all operations
        # Override in subclasses for specific authorization logic
        return ServiceResult.success_result()
    
    def log_operation(
        self,
        operation: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log service operation for audit and debugging.
        
        Args:
            operation: Operation name
            user_id: User who performed the operation
            resource_id: Resource affected by the operation
            success: Whether operation succeeded
            error: Error message if operation failed
            metadata: Additional metadata to log
        """
        log_data = {
            "operation": operation,
            "user_id": user_id,
            "resource_id": resource_id,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        if success:
            self.logger.info("Service operation completed", **log_data)
        else:
            log_data["error"] = error
            self.logger.error("Service operation failed", **log_data)


class CRUDService(BaseService[T]):
    """
    Base service for Create, Read, Update, Delete operations.
    
    Provides standard CRUD patterns with proper error handling
    and business logic validation.
    """
    
    @abstractmethod
    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> ServiceResult:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            user_id: User creating the entity
            
        Returns:
            ServiceResult containing the created entity or error
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str, user_id: Optional[str] = None) -> ServiceResult:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity identifier
            user_id: User requesting the entity
            
        Returns:
            ServiceResult containing the entity or error
        """
        pass
    
    @abstractmethod
    async def update(
        self, 
        entity_id: str, 
        updates: Dict[str, Any], 
        user_id: Optional[str] = None
    ) -> ServiceResult:
        """
        Update an entity.
        
        Args:
            entity_id: Entity identifier
            updates: Fields to update
            user_id: User performing the update
            
        Returns:
            ServiceResult containing the updated entity or error
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str, user_id: Optional[str] = None) -> ServiceResult:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity identifier
            user_id: User performing the deletion
            
        Returns:
            ServiceResult indicating success or failure
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        user_id: Optional[str] = None
    ) -> ServiceResult:
        """
        List entities with filtering and pagination.
        
        Args:
            filters: Filter criteria
            page: Page number (1-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            user_id: User requesting the list
            
        Returns:
            ServiceResult containing PaginatedResult or error
        """
        pass


class ValidationMixin:
    """
    Mixin providing common validation utilities for services.
    """
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> ServiceResult:
        """
        Validate that required fields are present and not empty.
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            ServiceResult indicating validation success or failure
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            return ServiceResult.error_result(
                error=f"Missing required fields: {', '.join(missing_fields)}",
                error_code="MISSING_REQUIRED_FIELDS",
                metadata={"missing_fields": missing_fields}
            )
        
        return ServiceResult.success_result()
    
    def validate_field_types(self, data: Dict[str, Any], field_types: Dict[str, type]) -> ServiceResult:
        """
        Validate that fields have the correct types.
        
        Args:
            data: Data to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            ServiceResult indicating validation success or failure
        """
        type_errors = []
        
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append({
                        "field": field,
                        "expected": expected_type.__name__,
                        "actual": type(data[field]).__name__
                    })
        
        if type_errors:
            return ServiceResult.error_result(
                error="Field type validation failed",
                error_code="INVALID_FIELD_TYPES",
                metadata={"type_errors": type_errors}
            )
        
        return ServiceResult.success_result()
    
    def validate_string_length(
        self, 
        value: str, 
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> ServiceResult:
        """
        Validate string length constraints.
        
        Args:
            value: String value to validate
            field_name: Name of the field being validated
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            ServiceResult indicating validation success or failure
        """
        if min_length is not None and len(value) < min_length:
            return ServiceResult.error_result(
                error=f"{field_name} must be at least {min_length} characters",
                error_code="STRING_TOO_SHORT",
                metadata={"field": field_name, "min_length": min_length, "actual_length": len(value)}
            )
        
        if max_length is not None and len(value) > max_length:
            return ServiceResult.error_result(
                error=f"{field_name} must be no more than {max_length} characters",
                error_code="STRING_TOO_LONG",
                metadata={"field": field_name, "max_length": max_length, "actual_length": len(value)}
            )
        
        return ServiceResult.success_result()
    
    def validate_email(self, email: str) -> ServiceResult:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            ServiceResult indicating validation success or failure
        """
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return ServiceResult.error_result(
                error="Invalid email format",
                error_code="INVALID_EMAIL_FORMAT",
                metadata={"email": email}
            )
        
        return ServiceResult.success_result()


class AuthorizationMixin:
    """
    Mixin providing common authorization utilities for services.
    """
    
    async def require_user_access(
        self, 
        user_id: str, 
        resource_user_id: str, 
        operation: str
    ) -> ServiceResult:
        """
        Require that user has access to their own resources.
        
        Args:
            user_id: User making the request
            resource_user_id: User who owns the resource
            operation: Operation being performed
            
        Returns:
            ServiceResult indicating authorization success or failure
        """
        if user_id != resource_user_id:
            return ServiceResult.error_result(
                error=f"Unauthorized to {operation} resource owned by another user",
                error_code="UNAUTHORIZED_ACCESS",
                metadata={"operation": operation, "user_id": user_id, "resource_user_id": resource_user_id}
            )
        
        return ServiceResult.success_result()
    
    async def require_admin_access(self, user_id: str, operation: str) -> ServiceResult:
        """
        Require that user has admin privileges.
        
        Args:
            user_id: User making the request
            operation: Operation being performed
            
        Returns:
            ServiceResult indicating authorization success or failure
        """
        # This would typically check user roles/permissions
        # Implementation depends on user model and permission system
        
        # For now, placeholder implementation
        return ServiceResult.error_result(
            error=f"Admin privileges required for {operation}",
            error_code="ADMIN_REQUIRED",
            metadata={"operation": operation, "user_id": user_id}
        )


class CacheableMixin:
    """
    Mixin providing caching utilities for services.
    """
    
    def __init__(self):
        super().__init__()
        self._cache = {}
    
    def get_cache_key(self, operation: str, **params) -> str:
        """
        Generate cache key for an operation.
        
        Args:
            operation: Operation name
            **params: Parameters that affect the result
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        key_data = f"{operation}:{json.dumps(sorted_params)}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def cache_result(self, key: str, result: Any, ttl_seconds: int = 300) -> None:
        """
        Cache a result with TTL.
        
        Args:
            key: Cache key
            result: Result to cache
            ttl_seconds: Time to live in seconds
        """
        expires_at = datetime.utcnow().timestamp() + ttl_seconds
        self._cache[key] = {
            "result": result,
            "expires_at": expires_at
        }
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """
        Get cached result if still valid.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if expired/missing
        """
        if key not in self._cache:
            return None
        
        cached = self._cache[key]
        
        if datetime.utcnow().timestamp() > cached["expires_at"]:
            del self._cache[key]
            return None
        
        return cached["result"]
    
    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys (simple string contains)
        """
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]