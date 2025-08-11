"""
Security audit logging system.
Tracks all sensitive operations for compliance and security monitoring.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid

from investment_system.infrastructure.database import get_db_manager, AuditLog
from investment_system.infrastructure.crud import AuditLogCRUD


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class AuditLogger:
    """
    Secure audit logging for compliance.
    Logs to both database and file for redundancy.
    """
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_path: Path to audit log file (optional)
        """
        self.log_path = Path(log_path) if log_path else Path("runtime/audit")
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.db_manager = get_db_manager()
    
    def log_event(
        self,
        event_type: str,
        event_category: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_score: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        """
        Log security-relevant event to database and file.
        
        Args:
            event_type: Type of event (login, api_call, etc.)
            event_category: Category (auth, api, billing, security)
            user_id: User ID if applicable
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional event details
            risk_score: Risk score (0-100)
            request_id: Request correlation ID
        """
        # Sanitize details to remove sensitive data
        sanitized_details = self._sanitize_details(details or {})
        
        # Calculate risk score if not provided
        if risk_score is None:
            risk_score = self._calculate_risk_score(
                event_type, event_category, sanitized_details
            )
        
        # Create event record
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "event_category": event_category,
            "user_id": user_id,
            "ip_address": self._hash_ip(ip_address) if ip_address else None,
            "user_agent": user_agent,
            "request_id": request_id or str(uuid.uuid4()),
            "details": sanitized_details,
            "risk_score": risk_score,
            "flagged": risk_score > 70
        }
        
        # Add integrity checksum
        event["checksum"] = self._calculate_checksum(event)
        
        # Log to database
        try:
            with self.db_manager as db:
                AuditLogCRUD.log_event(
                    db=db,
                    event_type=event_type,
                    event_category=event_category,
                    user_id=uuid.UUID(user_id) if user_id else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=sanitized_details,
                    risk_score=risk_score
                )
        except Exception as e:
            logger.error("Failed to log to database", error=str(e))
        
        # Log to file (append-only for integrity)
        try:
            log_file = self.log_path / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.log"
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error("Failed to log to file", error=str(e))
        
        # Log high-risk events to structured logger
        if risk_score > 70:
            logger.warning(
                "High risk event detected",
                **event
            )
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """
        Remove sensitive data from event details.
        
        Args:
            details: Original event details
            
        Returns:
            Sanitized details
        """
        sensitive_keys = [
            "password", "token", "secret", "key", "credit_card",
            "ssn", "api_key", "jwt", "authorization", "cookie"
        ]
        
        sanitized = {}
        for key, value in details.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _hash_ip(self, ip: str) -> str:
        """
        Hash IP address for privacy.
        
        Args:
            ip: IP address
            
        Returns:
            Hashed IP (first 16 chars)
        """
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def _calculate_risk_score(
        self,
        event_type: str,
        event_category: str,
        details: Dict
    ) -> int:
        """
        Calculate risk score for event.
        
        Args:
            event_type: Type of event
            event_category: Event category
            details: Event details
            
        Returns:
            Risk score (0-100)
        """
        score = 0
        
        # High risk event types
        high_risk_events = [
            "failed_login", "permission_denied", "rate_limit_exceeded",
            "invalid_token", "suspicious_activity", "data_breach"
        ]
        
        if event_type in high_risk_events:
            score += 50
        
        # Security category events
        if event_category == "security":
            score += 30
        
        # Multiple failed attempts
        if details.get("failed_attempts", 0) > 3:
            score += 20
        
        # Unusual time (outside business hours)
        hour = datetime.utcnow().hour
        if hour < 6 or hour > 22:
            score += 10
        
        # SQL injection attempts
        if any(keyword in str(details).upper() for keyword in 
               ["DROP", "DELETE", "INSERT", "UPDATE", "UNION", "SELECT"]):
            score += 40
        
        return min(score, 100)
    
    def _calculate_checksum(self, event: Dict) -> str:
        """
        Calculate integrity checksum for event.
        
        Args:
            event: Event data
            
        Returns:
            SHA256 checksum
        """
        # Remove checksum field if present
        event_copy = {k: v for k, v in event.items() if k != "checksum"}
        event_str = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log all API requests for audit.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.audit_logger = AuditLogger()
    
    async def dispatch(self, request: Request, call_next):
        """
        Log request and response for audit trail.
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request details
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Start timer
        start_time = datetime.utcnow()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Determine event category
        path = request.url.path
        if path.startswith("/auth"):
            category = "auth"
        elif path.startswith("/api"):
            category = "api"
        elif path.startswith("/billing"):
            category = "billing"
        else:
            category = "general"
        
        # Log the request
        self.audit_logger.log_event(
            event_type=f"{request.method}_{path}",
            event_category=category,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            details={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "response_time": response_time,
                "query_params": dict(request.query_params)
            },
            request_id=request_id
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class SecurityEventLogger:
    """
    Specialized logger for security events.
    """
    
    def __init__(self):
        self.audit_logger = AuditLogger()
    
    def log_login_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None
    ):
        """Log login attempt."""
        self.audit_logger.log_event(
            event_type="login_attempt" if success else "failed_login",
            event_category="auth",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "success": success,
                "failure_reason": failure_reason
            },
            risk_score=0 if success else 60
        )
    
    def log_api_key_usage(
        self,
        api_key_id: str,
        user_id: str,
        endpoint: str,
        ip_address: str
    ):
        """Log API key usage."""
        self.audit_logger.log_event(
            event_type="api_key_usage",
            event_category="api",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "api_key_id": api_key_id,
                "endpoint": endpoint
            }
        )
    
    def log_rate_limit_exceeded(
        self,
        user_id: Optional[str],
        ip_address: str,
        endpoint: str,
        limit: int
    ):
        """Log rate limit violation."""
        self.audit_logger.log_event(
            event_type="rate_limit_exceeded",
            event_category="security",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "endpoint": endpoint,
                "limit": limit
            },
            risk_score=70
        )
    
    def log_suspicious_activity(
        self,
        description: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict[str, Any]
    ):
        """Log suspicious activity."""
        self.audit_logger.log_event(
            event_type="suspicious_activity",
            event_category="security",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "description": description,
                **details
            },
            risk_score=80
        )


# Global security event logger instance
security_logger = SecurityEventLogger()