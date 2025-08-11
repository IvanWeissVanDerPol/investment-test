"""
Structured logging system with correlation ID support and performance monitoring.
"""

import sys
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'exc_info', 'exc_text', 'stack_info', 'correlation_id'
            }:
                try:
                    json.dumps(value)  # Test if value is JSON serializable
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationIDProcessor:
    """Structlog processor to add correlation ID to log entries."""
    
    def __call__(self, logger, name, event_dict):
        correlation_id = structlog.contextvars.get_context().get('correlation_id')
        if correlation_id:
            event_dict['correlation_id'] = correlation_id
        return event_dict


class SanitizationProcessor:
    """Structlog processor to sanitize sensitive data from logs."""
    
    SENSITIVE_KEYS = {
        'password', 'token', 'secret', 'key', 'authorization',
        'api_key', 'jwt', 'stripe_key', 'database_url'
    }
    
    def __call__(self, logger, name, event_dict):
        return self._sanitize_dict(event_dict)
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data."""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive information
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings that might contain sensitive data
                sanitized[key] = value[:100] + "...TRUNCATED"
            else:
                sanitized[key] = value
        
        return sanitized


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Logging format ('json' or 'console')
    """
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        CorrelationIDProcessor(),
        SanitizationProcessor(),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if log_format.lower() == "json":
        processors.extend([
            structlog.processors.JSONRenderer(ensure_ascii=False)
        ])
    else:
        # Console format for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Set up JSON formatter for stdlib logging when using JSON format
    if log_format.lower() == "json":
        root_logger = logging.getLogger()
        if root_logger.handlers:
            root_logger.handlers[0].setFormatter(JSONFormatter())


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **context):
        self.context = context
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.clear_contextvars()


class PerformanceLogger:
    """Logger for tracking performance metrics."""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log API request metrics."""
        self.logger.info(
            "API request completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
            user_agent=user_agent,
            metric_type="api_request"
        )
    
    def log_database_query(
        self,
        query_type: str,
        table: Optional[str],
        duration_ms: float,
        rows_affected: Optional[int] = None
    ) -> None:
        """Log database query metrics."""
        self.logger.debug(
            "Database query executed",
            query_type=query_type,
            table=table,
            duration_ms=round(duration_ms, 2),
            rows_affected=rows_affected,
            metric_type="database_query"
        )
    
    def log_external_service_call(
        self,
        service: str,
        operation: str,
        duration_ms: float,
        status_code: Optional[int] = None,
        success: bool = True
    ) -> None:
        """Log external service call metrics."""
        self.logger.info(
            "External service call completed",
            service=service,
            operation=operation,
            duration_ms=round(duration_ms, 2),
            status_code=status_code,
            success=success,
            metric_type="external_service_call"
        )
    
    def log_business_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log business logic events."""
        self.logger.info(
            "Business event occurred",
            event_type=event_type,
            user_id=user_id,
            details=details or {},
            metric_type="business_event"
        )


class SecurityLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger
    
    def log_authentication_attempt(
        self,
        email: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempts."""
        self.logger.warning(
            "Authentication attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
            security_event="authentication_attempt"
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log authorization failures."""
        self.logger.warning(
            "Authorization failure",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            security_event="authorization_failure"
        )
    
    def log_rate_limit_violation(
        self,
        ip_address: Optional[str],
        endpoint: str,
        limit: str,
        user_id: Optional[str] = None
    ) -> None:
        """Log rate limit violations."""
        self.logger.warning(
            "Rate limit exceeded",
            ip_address=ip_address,
            endpoint=endpoint,
            limit=limit,
            user_id=user_id,
            security_event="rate_limit_violation"
        )
    
    def log_suspicious_activity(
        self,
        user_id: Optional[str],
        activity: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> None:
        """Log suspicious activities."""
        self.logger.error(
            "Suspicious activity detected",
            user_id=user_id,
            activity=activity,
            details=details,
            ip_address=ip_address,
            security_event="suspicious_activity"
        )


# Convenience functions
def with_context(**context):
    """Decorator to add context to all log messages in a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LogContext(**context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_function_call(logger: structlog.stdlib.BoundLogger):
    """Decorator to automatically log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling function {func.__name__}",
                function=func.__name__,
                module=func.__module__,
                args=len(args),
                kwargs=list(kwargs.keys())
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Function {func.__name__} completed successfully",
                    function=func.__name__
                )
                return result
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed",
                    function=func.__name__,
                    error=str(e),
                    exception_type=type(e).__name__
                )
                raise
        return wrapper
    return decorator