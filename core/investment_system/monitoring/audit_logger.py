"""
Comprehensive Audit Logging System
Tracks all user actions, system events, and security incidents
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
import inspect
from functools import wraps
import structlog
from flask import request, g
import os

from ..utils.secure_config_manager import get_config_manager
from ..database.connection_manager import get_connection_manager


class EventType(Enum):
    """Audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"
    
    # Portfolio events
    PORTFOLIO_VIEWED = "portfolio_viewed"
    PORTFOLIO_MODIFIED = "portfolio_modified"
    POSITION_ADDED = "position_added"
    POSITION_MODIFIED = "position_modified"
    POSITION_REMOVED = "position_removed"
    
    # Trading events
    ORDER_PLACED = "order_placed"
    ORDER_MODIFIED = "order_modified"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_EXECUTED = "order_executed"
    
    # Analysis events
    ANALYSIS_REQUESTED = "analysis_requested"
    ANALYSIS_COMPLETED = "analysis_completed"
    AI_PREDICTION_GENERATED = "ai_prediction_generated"
    
    # Data events
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGED = "config_changed"
    ERROR_OCCURRED = "error_occurred"
    
    # API events
    API_CALL = "api_call"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class SeverityLevel(Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Individual audit event"""
    event_id: str
    timestamp: datetime
    event_type: EventType
    severity: SeverityLevel
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'action': self.action,
            'details': self.details or {},
            'success': self.success,
            'error_message': self.error_message,
            'request_id': self.request_id
        }


class AuditLogger:
    """
    Comprehensive audit logging system with multiple storage backends
    """
    
    def __init__(self):
        """Initialize audit logger"""
        self.config = get_config_manager()
        self.db_manager = get_connection_manager()
        
        # Set up structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger("audit")
        
        # Initialize audit table
        self._initialize_audit_table()
    
    def _initialize_audit_table(self):
        """Initialize audit log table in database"""
        try:
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS audit_log (
                    event_id VARCHAR(36) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(10) NOT NULL,
                    user_id VARCHAR(36),
                    session_id VARCHAR(36),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    resource VARCHAR(100),
                    action VARCHAR(50),
                    details JSONB,
                    success BOOLEAN NOT NULL DEFAULT TRUE,
                    error_message TEXT,
                    request_id VARCHAR(36),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_log(severity);
            """
            
            # For SQLite, use TEXT instead of JSONB
            if not self.db_manager.is_postgresql:
                create_table_sql = create_table_sql.replace('JSONB', 'TEXT')
                create_table_sql = create_table_sql.replace('VARCHAR(36)', 'TEXT')
                create_table_sql = create_table_sql.replace('VARCHAR(50)', 'TEXT')
                create_table_sql = create_table_sql.replace('VARCHAR(10)', 'TEXT')
                create_table_sql = create_table_sql.replace('VARCHAR(45)', 'TEXT')
                create_table_sql = create_table_sql.replace('VARCHAR(100)', 'TEXT')
            
            self.db_manager.execute_query(create_table_sql)
            
        except Exception as e:
            self.logger.error("Failed to initialize audit table", error=str(e))
    
    def log_event(self, event_type: EventType, severity: SeverityLevel = SeverityLevel.MEDIUM,
                  user_id: str = None, resource: str = None, action: str = None,
                  details: Dict[str, Any] = None, success: bool = True,
                  error_message: str = None) -> str:
        """Log an audit event"""
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Extract request context if available
        ip_address = None
        user_agent = None
        session_id = None
        request_id = None
        
        try:
            if request:
                ip_address = request.remote_addr
                user_agent = request.user_agent.string
                request_id = getattr(request, 'id', None)
                
            if hasattr(g, 'current_user'):
                user_id = user_id or g.current_user.user_id
                session_id = getattr(g, 'session_id', None)
                
        except RuntimeError:
            # Outside request context
            pass
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            success=success,
            error_message=error_message,
            request_id=request_id
        )
        
        # Log to structured logger
        log_data = event.to_dict()
        
        if severity == SeverityLevel.CRITICAL:
            self.logger.critical("Audit event", **log_data)
        elif severity == SeverityLevel.HIGH:
            self.logger.error("Audit event", **log_data)
        elif severity == SeverityLevel.MEDIUM:
            self.logger.warning("Audit event", **log_data)
        else:
            self.logger.info("Audit event", **log_data)
        
        # Store in database
        self._store_event_in_db(event)
        
        # Check for security alerts
        self._check_security_alerts(event)
        
        return event_id
    
    def _store_event_in_db(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            insert_sql = """
                INSERT INTO audit_log (
                    event_id, timestamp, event_type, severity, user_id, session_id,
                    ip_address, user_agent, resource, action, details, success,
                    error_message, request_id
                ) VALUES (
                    :event_id, :timestamp, :event_type, :severity, :user_id, :session_id,
                    :ip_address, :user_agent, :resource, :action, :details, :success,
                    :error_message, :request_id
                )
            """
            
            # Prepare details as JSON string for SQLite
            details_json = json.dumps(event.details) if event.details else None
            
            params = {
                'event_id': event.event_id,
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'severity': event.severity.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'resource': event.resource,
                'action': event.action,
                'details': details_json,
                'success': event.success,
                'error_message': event.error_message,
                'request_id': event.request_id
            }
            
            self.db_manager.execute_query(insert_sql, params)
            
        except Exception as e:
            self.logger.error("Failed to store audit event in database", 
                            event_id=event.event_id, error=str(e))
    
    def _check_security_alerts(self, event: AuditEvent):
        """Check for security alerts and patterns"""
        
        # Check for multiple failed logins
        if event.event_type == EventType.LOGIN_FAILURE:
            self._check_failed_login_pattern(event)
        
        # Check for suspicious API usage
        if event.event_type == EventType.RATE_LIMIT_EXCEEDED:
            self._alert_rate_limit_abuse(event)
        
        # Check for privilege escalation attempts
        if event.event_type == EventType.PERMISSION_DENIED and event.severity == SeverityLevel.HIGH:
            self._alert_privilege_escalation(event)
    
    def _check_failed_login_pattern(self, event: AuditEvent):
        """Check for suspicious login failure patterns"""
        try:
            # Count failed logins from same IP in last 10 minutes
            query = """
                SELECT COUNT(*) FROM audit_log 
                WHERE event_type = :event_type 
                AND ip_address = :ip_address 
                AND timestamp > :time_threshold
            """
            
            threshold = datetime.utcnow().replace(minute=datetime.utcnow().minute-10)
            params = {
                'event_type': EventType.LOGIN_FAILURE.value,
                'ip_address': event.ip_address,
                'time_threshold': threshold
            }
            
            result = self.db_manager.execute_query(query, params)
            count = result[0][0] if result else 0
            
            if count > 5:  # More than 5 failures in 10 minutes
                self.log_event(
                    EventType.SUSPICIOUS_ACTIVITY,
                    SeverityLevel.HIGH,
                    details={
                        'pattern': 'multiple_failed_logins',
                        'ip_address': event.ip_address,
                        'count': count,
                        'time_window': '10_minutes'
                    }
                )
                
        except Exception as e:
            self.logger.error("Failed to check login failure pattern", error=str(e))
    
    def _alert_rate_limit_abuse(self, event: AuditEvent):
        """Alert on rate limit abuse"""
        self.log_event(
            EventType.SUSPICIOUS_ACTIVITY,
            SeverityLevel.HIGH,
            user_id=event.user_id,
            details={
                'pattern': 'rate_limit_abuse',
                'resource': event.resource,
                'ip_address': event.ip_address
            }
        )
    
    def _alert_privilege_escalation(self, event: AuditEvent):
        """Alert on potential privilege escalation"""
        self.log_event(
            EventType.SUSPICIOUS_ACTIVITY,
            SeverityLevel.CRITICAL,
            user_id=event.user_id,
            details={
                'pattern': 'privilege_escalation_attempt',
                'resource': event.resource,
                'action': event.action
            }
        )
    
    def get_events(self, user_id: str = None, event_type: EventType = None,
                   start_time: datetime = None, end_time: datetime = None,
                   severity: SeverityLevel = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit events with filtering"""
        
        try:
            query_parts = ["SELECT * FROM audit_log WHERE 1=1"]
            params = {}
            
            if user_id:
                query_parts.append("AND user_id = :user_id")
                params['user_id'] = user_id
            
            if event_type:
                query_parts.append("AND event_type = :event_type")
                params['event_type'] = event_type.value
            
            if start_time:
                query_parts.append("AND timestamp >= :start_time")
                params['start_time'] = start_time
            
            if end_time:
                query_parts.append("AND timestamp <= :end_time")
                params['end_time'] = end_time
            
            if severity:
                query_parts.append("AND severity = :severity")
                params['severity'] = severity.value
            
            query_parts.append("ORDER BY timestamp DESC")
            query_parts.append(f"LIMIT {limit}")
            
            query = " ".join(query_parts)
            results = self.db_manager.execute_query(query, params)
            
            # Convert results to dictionaries
            events = []
            for row in results:
                event_dict = {
                    'event_id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'severity': row[3],
                    'user_id': row[4],
                    'session_id': row[5],
                    'ip_address': row[6],
                    'user_agent': row[7],
                    'resource': row[8],
                    'action': row[9],
                    'details': json.loads(row[10]) if row[10] else {},
                    'success': row[11],
                    'error_message': row[12],
                    'request_id': row[13]
                }
                events.append(event_dict)
            
            return events
            
        except Exception as e:
            self.logger.error("Failed to retrieve audit events", error=str(e))
            return []
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security event summary for specified time period"""
        
        try:
            threshold = datetime.utcnow().replace(hour=datetime.utcnow().hour-hours)
            
            # Get event counts by type
            query = """
                SELECT event_type, severity, COUNT(*) as count
                FROM audit_log 
                WHERE timestamp > :threshold
                GROUP BY event_type, severity
                ORDER BY count DESC
            """
            
            results = self.db_manager.execute_query(query, {'threshold': threshold})
            
            summary = {
                'time_period_hours': hours,
                'total_events': 0,
                'events_by_type': {},
                'events_by_severity': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                'security_incidents': 0
            }
            
            for row in results:
                event_type, severity, count = row
                summary['total_events'] += count
                summary['events_by_severity'][severity] += count
                
                if event_type not in summary['events_by_type']:
                    summary['events_by_type'][event_type] = 0
                summary['events_by_type'][event_type] += count
                
                # Count security incidents
                if event_type in [EventType.SECURITY_VIOLATION.value, 
                                EventType.SUSPICIOUS_ACTIVITY.value]:
                    summary['security_incidents'] += count
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to generate security summary", error=str(e))
            return {}


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(event_type: EventType, severity: SeverityLevel = SeverityLevel.MEDIUM,
             **kwargs) -> str:
    """Convenience function to log audit event"""
    return get_audit_logger().log_event(event_type, severity, **kwargs)


def audit_decorator(event_type: EventType, severity: SeverityLevel = SeverityLevel.MEDIUM,
                   resource: str = None):
    """Decorator to automatically audit function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            function_name = f"{func.__module__}.{func.__name__}"
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful execution
                audit_log(
                    event_type,
                    severity,
                    resource=resource or function_name,
                    action='execute',
                    details={
                        'function': function_name,
                        'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    },
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log failed execution
                audit_log(
                    EventType.ERROR_OCCURRED,
                    SeverityLevel.HIGH,
                    resource=resource or function_name,
                    action='execute',
                    details={
                        'function': function_name,
                        'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                        'exception_type': type(e).__name__
                    },
                    success=False,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test audit logging
    logger = AuditLogger()
    
    # Test various event types
    event_id = logger.log_event(
        EventType.LOGIN_SUCCESS,
        SeverityLevel.LOW,
        user_id="test-user-123",
        details={'login_method': 'password'}
    )
    print(f"Logged event: {event_id}")
    
    # Test security event
    logger.log_event(
        EventType.SUSPICIOUS_ACTIVITY,
        SeverityLevel.HIGH,
        details={'pattern': 'test_pattern'}
    )
    
    # Get recent events
    events = logger.get_events(limit=10)
    print(f"Retrieved {len(events)} events")
    
    # Get security summary
    summary = logger.get_security_summary()
    print(f"Security summary: {summary}")