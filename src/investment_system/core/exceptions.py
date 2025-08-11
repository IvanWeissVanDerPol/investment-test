"""
Core exception handling system with standardized error codes and responses.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class ErrorCode(Enum):
    """Standardized error codes for the application."""
    
    # General errors (1000-1099)
    INTERNAL_ERROR = ("INTERNAL_ERROR", 500, "An internal error occurred")
    SERVICE_UNAVAILABLE = ("SERVICE_UNAVAILABLE", 503, "Service is temporarily unavailable")
    NOT_IMPLEMENTED = ("NOT_IMPLEMENTED", 501, "Feature not implemented")
    MAINTENANCE_MODE = ("MAINTENANCE_MODE", 503, "System is under maintenance")
    
    # Validation errors (1100-1199)
    VALIDATION_ERROR = ("VALIDATION_ERROR", 400, "Request validation failed")
    INVALID_INPUT = ("INVALID_INPUT", 400, "Invalid input provided")
    MISSING_REQUIRED_FIELD = ("MISSING_REQUIRED_FIELD", 400, "Required field is missing")
    INVALID_FORMAT = ("INVALID_FORMAT", 400, "Invalid data format")
    VALUE_OUT_OF_RANGE = ("VALUE_OUT_OF_RANGE", 400, "Value is out of acceptable range")
    
    # Authentication errors (1200-1299)
    AUTHENTICATION_REQUIRED = ("AUTHENTICATION_REQUIRED", 401, "Authentication is required")
    AUTHENTICATION_FAILED = ("AUTHENTICATION_FAILED", 401, "Authentication failed")
    INVALID_TOKEN = ("INVALID_TOKEN", 401, "Invalid or expired token")
    TOKEN_EXPIRED = ("TOKEN_EXPIRED", 401, "Token has expired")
    INVALID_CREDENTIALS = ("INVALID_CREDENTIALS", 401, "Invalid credentials provided")
    
    # Authorization errors (1300-1399)
    AUTHORIZATION_FAILED = ("AUTHORIZATION_FAILED", 403, "Insufficient permissions")
    ACCESS_DENIED = ("ACCESS_DENIED", 403, "Access to resource denied")
    SUBSCRIPTION_REQUIRED = ("SUBSCRIPTION_REQUIRED", 402, "Valid subscription required")
    TIER_UPGRADE_REQUIRED = ("TIER_UPGRADE_REQUIRED", 402, "Higher tier subscription required")
    FEATURE_DISABLED = ("FEATURE_DISABLED", 403, "Feature is disabled for your account")
    
    # Rate limiting errors (1400-1499)
    RATE_LIMIT_EXCEEDED = ("RATE_LIMIT_EXCEEDED", 429, "Rate limit exceeded")
    QUOTA_EXCEEDED = ("QUOTA_EXCEEDED", 429, "Usage quota exceeded")
    REQUEST_TOO_LARGE = ("REQUEST_TOO_LARGE", 413, "Request payload too large")
    TOO_MANY_REQUESTS = ("TOO_MANY_REQUESTS", 429, "Too many requests")
    
    # Resource errors (1500-1599)
    RESOURCE_NOT_FOUND = ("RESOURCE_NOT_FOUND", 404, "Requested resource not found")
    RESOURCE_ALREADY_EXISTS = ("RESOURCE_ALREADY_EXISTS", 409, "Resource already exists")
    RESOURCE_CONFLICT = ("RESOURCE_CONFLICT", 409, "Resource conflict occurred")
    RESOURCE_LOCKED = ("RESOURCE_LOCKED", 423, "Resource is locked")
    RESOURCE_EXPIRED = ("RESOURCE_EXPIRED", 410, "Resource has expired")
    
    # Business logic errors (1600-1699)
    INSUFFICIENT_BALANCE = ("INSUFFICIENT_BALANCE", 400, "Insufficient account balance")
    INVALID_SYMBOL = ("INVALID_SYMBOL", 400, "Invalid trading symbol")
    MARKET_CLOSED = ("MARKET_CLOSED", 400, "Market is currently closed")
    INVALID_ORDER = ("INVALID_ORDER", 400, "Invalid order parameters")
    TRADING_SUSPENDED = ("TRADING_SUSPENDED", 400, "Trading is suspended for this symbol")
    
    # External service errors (1700-1799)
    EXTERNAL_SERVICE_ERROR = ("EXTERNAL_SERVICE_ERROR", 502, "External service error")
    PAYMENT_PROCESSOR_ERROR = ("PAYMENT_PROCESSOR_ERROR", 502, "Payment processor error")
    DATA_PROVIDER_ERROR = ("DATA_PROVIDER_ERROR", 502, "Market data provider error")
    NOTIFICATION_SERVICE_ERROR = ("NOTIFICATION_SERVICE_ERROR", 502, "Notification service error")
    
    # Database errors (1800-1899)
    DATABASE_ERROR = ("DATABASE_ERROR", 500, "Database operation failed")
    CONNECTION_ERROR = ("CONNECTION_ERROR", 500, "Database connection failed")
    TRANSACTION_ERROR = ("TRANSACTION_ERROR", 500, "Database transaction failed")
    CONSTRAINT_VIOLATION = ("CONSTRAINT_VIOLATION", 400, "Database constraint violation")
    
    # User account errors (1900-1999)
    USER_NOT_FOUND = ("USER_NOT_FOUND", 404, "User account not found")
    USER_ALREADY_EXISTS = ("USER_ALREADY_EXISTS", 409, "User account already exists")
    ACCOUNT_SUSPENDED = ("ACCOUNT_SUSPENDED", 403, "Account is suspended")
    ACCOUNT_EXPIRED = ("ACCOUNT_EXPIRED", 403, "Account has expired")
    EMAIL_NOT_VERIFIED = ("EMAIL_NOT_VERIFIED", 403, "Email address not verified")
    PASSWORD_RESET_REQUIRED = ("PASSWORD_RESET_REQUIRED", 403, "Password reset required")
    
    @property
    def code(self) -> str:
        return self.value[0]
    
    @property
    def http_status(self) -> int:
        return self.value[1]
    
    @property
    def default_message(self) -> str:
        return self.value[2]
    
    def __str__(self) -> str:
        return self.code


@dataclass
class ErrorContext:
    """Additional context for error reporting."""
    field: Optional[str] = None
    constraint: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None


class APIError(Exception):
    """
    Base exception for API errors with structured error information.
    
    This exception provides a standardized way to handle errors throughout
    the application with proper error codes, messages, and context.
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        self.code = code
        self.message = message or code.default_message
        self.details = details or {}
        self.context = context
        self.cause = cause
        
        # Add context to details if provided
        if context:
            context_dict = {
                k: v for k, v in context.__dict__.items() 
                if v is not None
            }
            self.details.update(context_dict)
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "http_status": self.code.http_status
        }
    
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
    
    def __repr__(self) -> str:
        return f"APIError(code={self.code.value}, message='{self.message}')"


class ValidationError(APIError):
    """Exception for request validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        context = ErrorContext(
            field=field,
            expected=expected,
            actual=actual
        )
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            context=context
        )


class AuthenticationError(APIError):
    """Exception for authentication failures."""
    
    def __init__(
        self,
        message: Optional[str] = None,
        code: ErrorCode = ErrorCode.AUTHENTICATION_FAILED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details
        )


class AuthorizationError(APIError):
    """Exception for authorization failures."""
    
    def __init__(
        self,
        message: Optional[str] = None,
        required_permission: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        context = ErrorContext(
            resource_type=resource_type,
            resource_id=resource_id
        )
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            code=ErrorCode.AUTHORIZATION_FAILED,
            message=message,
            details=details,
            context=context
        )


class RateLimitError(APIError):
    """Exception for rate limit violations."""
    
    def __init__(
        self,
        message: Optional[str] = None,
        limit: Optional[str] = None,
        reset_time: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        details = {}
        if limit:
            details["limit"] = limit
        if reset_time:
            details["reset_time"] = reset_time
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details
        )


class ResourceNotFoundError(APIError):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        if not message:
            if resource_id:
                message = f"{resource_type} with ID '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"
        
        context = ErrorContext(
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            context=context
        )


class ConflictError(APIError):
    """Exception for resource conflict errors."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        constraint: Optional[str] = None
    ):
        context = ErrorContext(
            resource_type=resource_type,
            resource_id=resource_id,
            constraint=constraint
        )
        
        super().__init__(
            code=ErrorCode.RESOURCE_CONFLICT,
            message=message,
            context=context
        )


class ServiceUnavailableError(APIError):
    """Exception for service unavailability."""
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        message: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        if not message:
            message = f"Service {service_name} is unavailable" if service_name else "Service unavailable"
        
        details = {}
        if service_name:
            details["service"] = service_name
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            details=details
        )


class BusinessLogicError(APIError):
    """Exception for business logic violations."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details
        )


class ExternalServiceError(APIError):
    """Exception for external service failures."""
    
    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        if not message:
            message = f"External service '{service_name}' returned an error"
        
        details = {"service": service_name}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Truncate long responses
        
        super().__init__(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=message,
            details=details
        )


# Convenience functions for common errors
def not_found(resource_type: str, resource_id: Optional[str] = None) -> ResourceNotFoundError:
    """Create a resource not found error."""
    return ResourceNotFoundError(resource_type, resource_id)


def validation_error(message: str, field: Optional[str] = None) -> ValidationError:
    """Create a validation error."""
    return ValidationError(message, field=field)


def unauthorized(message: Optional[str] = None) -> AuthenticationError:
    """Create an authentication error."""
    return AuthenticationError(message)


def forbidden(message: Optional[str] = None, required_permission: Optional[str] = None) -> AuthorizationError:
    """Create an authorization error."""
    return AuthorizationError(message, required_permission=required_permission)


def rate_limited(limit: Optional[str] = None, retry_after: Optional[int] = None) -> RateLimitError:
    """Create a rate limit error."""
    return RateLimitError(limit=limit, retry_after=retry_after)


def conflict(message: str, resource_type: Optional[str] = None) -> ConflictError:
    """Create a conflict error."""
    return ConflictError(message, resource_type=resource_type)


def service_unavailable(service_name: Optional[str] = None, retry_after: Optional[int] = None) -> ServiceUnavailableError:
    """Create a service unavailable error."""
    return ServiceUnavailableError(service_name, retry_after=retry_after)