"""
Authentication Models
User, Role, and Permission models for the authentication system
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json


class RoleType(Enum):
    """User role types"""
    ADMIN = "admin"
    PREMIUM = "premium"
    BASIC = "basic"
    DEMO = "demo"


class PermissionType(Enum):
    """Permission types"""
    # Portfolio permissions
    VIEW_PORTFOLIO = "view_portfolio"
    EDIT_PORTFOLIO = "edit_portfolio"
    DELETE_PORTFOLIO = "delete_portfolio"
    
    # Analysis permissions
    RUN_QUICK_ANALYSIS = "run_quick_analysis"
    RUN_COMPREHENSIVE_ANALYSIS = "run_comprehensive_analysis"
    VIEW_AI_PREDICTIONS = "view_ai_predictions"
    
    # Trading permissions
    PLACE_ORDERS = "place_orders"
    VIEW_POSITIONS = "view_positions"
    MODIFY_ORDERS = "modify_orders"
    
    # System permissions
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_USERS = "manage_users"
    SYSTEM_ADMIN = "system_admin"
    
    # API permissions
    API_ACCESS = "api_access"
    UNLIMITED_API_CALLS = "unlimited_api_calls"


@dataclass
class Permission:
    """Individual permission"""
    type: PermissionType
    description: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Role:
    """User role with permissions"""
    name: RoleType
    display_name: str
    permissions: List[Permission]
    max_portfolio_value: Optional[float] = None
    max_api_calls_per_day: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class User:
    """User model"""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    username: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    
    # Authentication fields
    is_active: bool = True
    is_verified: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    
    # Role and permissions
    role: RoleType = RoleType.BASIC
    permissions: List[PermissionType] = field(default_factory=list)
    
    # Session management
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    
    # Portfolio configuration
    portfolio_balance: float = 900.0
    risk_tolerance: str = "medium"
    investment_goals: List[str] = field(default_factory=lambda: ["AI/robotics growth"])
    
    # Subscription and billing
    subscription_tier: str = "basic"
    subscription_expires: Optional[datetime] = None
    api_calls_used_today: int = 0
    api_calls_limit: int = 1000
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization setup"""
        if not self.permissions:
            self.permissions = self._get_default_permissions()
    
    def _get_default_permissions(self) -> List[PermissionType]:
        """Get default permissions based on role"""
        permission_mapping = {
            RoleType.ADMIN: [
                PermissionType.VIEW_PORTFOLIO,
                PermissionType.EDIT_PORTFOLIO,
                PermissionType.DELETE_PORTFOLIO,
                PermissionType.RUN_QUICK_ANALYSIS,
                PermissionType.RUN_COMPREHENSIVE_ANALYSIS,
                PermissionType.VIEW_AI_PREDICTIONS,
                PermissionType.PLACE_ORDERS,
                PermissionType.VIEW_POSITIONS,
                PermissionType.MODIFY_ORDERS,
                PermissionType.VIEW_SYSTEM_LOGS,
                PermissionType.MANAGE_USERS,
                PermissionType.SYSTEM_ADMIN,
                PermissionType.API_ACCESS,
                PermissionType.UNLIMITED_API_CALLS
            ],
            RoleType.PREMIUM: [
                PermissionType.VIEW_PORTFOLIO,
                PermissionType.EDIT_PORTFOLIO,
                PermissionType.RUN_QUICK_ANALYSIS,
                PermissionType.RUN_COMPREHENSIVE_ANALYSIS,
                PermissionType.VIEW_AI_PREDICTIONS,
                PermissionType.PLACE_ORDERS,
                PermissionType.VIEW_POSITIONS,
                PermissionType.MODIFY_ORDERS,
                PermissionType.API_ACCESS
            ],
            RoleType.BASIC: [
                PermissionType.VIEW_PORTFOLIO,
                PermissionType.EDIT_PORTFOLIO,
                PermissionType.RUN_QUICK_ANALYSIS,
                PermissionType.VIEW_POSITIONS,
                PermissionType.API_ACCESS
            ],
            RoleType.DEMO: [
                PermissionType.VIEW_PORTFOLIO,
                PermissionType.RUN_QUICK_ANALYSIS
            ]
        }
        return permission_mapping.get(self.role, [])
    
    def has_permission(self, permission: PermissionType) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == RoleType.ADMIN
    
    def is_premium(self) -> bool:
        """Check if user has premium access"""
        return self.role in [RoleType.ADMIN, RoleType.PREMIUM]
    
    def is_account_locked(self) -> bool:
        """Check if account is locked"""
        if self.account_locked_until is None:
            return False
        return datetime.now() < self.account_locked_until
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock account for specified duration"""
        self.account_locked_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.updated_at = datetime.now()
    
    def unlock_account(self):
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.now()
    
    def can_make_api_call(self) -> bool:
        """Check if user can make API call (rate limiting)"""
        if self.has_permission(PermissionType.UNLIMITED_API_CALLS):
            return True
        return self.api_calls_used_today < self.api_calls_limit
    
    def increment_api_usage(self):
        """Increment API usage counter"""
        self.api_calls_used_today += 1
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def reset_daily_api_usage(self):
        """Reset daily API usage (called by scheduler)"""
        self.api_calls_used_today = 0
        self.updated_at = datetime.now()
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'mfa_enabled': self.mfa_enabled,
            'role': self.role.value,
            'permissions': [p.value for p in self.permissions],
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'portfolio_balance': self.portfolio_balance,
            'risk_tolerance': self.risk_tolerance,
            'investment_goals': self.investment_goals,
            'subscription_tier': self.subscription_tier,
            'subscription_expires': self.subscription_expires.isoformat() if self.subscription_expires else None,
            'api_calls_used_today': self.api_calls_used_today,
            'api_calls_limit': self.api_calls_limit,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        # Convert string enums back to enum types
        if 'role' in data and isinstance(data['role'], str):
            data['role'] = RoleType(data['role'])
        
        if 'permissions' in data:
            data['permissions'] = [PermissionType(p) for p in data['permissions']]
        
        # Convert ISO strings back to datetime objects
        datetime_fields = ['last_login', 'last_activity', 'account_locked_until', 
                          'subscription_expires', 'created_at', 'updated_at']
        
        for field in datetime_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)


# Default role configurations
DEFAULT_ROLES = {
    RoleType.ADMIN: Role(
        name=RoleType.ADMIN,
        display_name="Administrator",
        permissions=[Permission(p, f"Admin permission: {p.value}") for p in PermissionType],
        max_portfolio_value=None,  # Unlimited
        max_api_calls_per_day=None  # Unlimited
    ),
    RoleType.PREMIUM: Role(
        name=RoleType.PREMIUM,
        display_name="Premium User",
        permissions=[
            Permission(PermissionType.VIEW_PORTFOLIO, "View portfolio"),
            Permission(PermissionType.EDIT_PORTFOLIO, "Edit portfolio"),
            Permission(PermissionType.RUN_QUICK_ANALYSIS, "Run quick analysis"),
            Permission(PermissionType.RUN_COMPREHENSIVE_ANALYSIS, "Run comprehensive analysis"),
            Permission(PermissionType.VIEW_AI_PREDICTIONS, "View AI predictions"),
            Permission(PermissionType.PLACE_ORDERS, "Place trading orders"),
            Permission(PermissionType.VIEW_POSITIONS, "View positions"),
            Permission(PermissionType.MODIFY_ORDERS, "Modify orders"),
            Permission(PermissionType.API_ACCESS, "API access")
        ],
        max_portfolio_value=100000.0,  # $100K limit
        max_api_calls_per_day=5000
    ),
    RoleType.BASIC: Role(
        name=RoleType.BASIC,
        display_name="Basic User",
        permissions=[
            Permission(PermissionType.VIEW_PORTFOLIO, "View portfolio"),
            Permission(PermissionType.EDIT_PORTFOLIO, "Edit portfolio"),
            Permission(PermissionType.RUN_QUICK_ANALYSIS, "Run quick analysis"),
            Permission(PermissionType.VIEW_POSITIONS, "View positions"),
            Permission(PermissionType.API_ACCESS, "Limited API access")
        ],
        max_portfolio_value=10000.0,  # $10K limit
        max_api_calls_per_day=1000
    ),
    RoleType.DEMO: Role(
        name=RoleType.DEMO,
        display_name="Demo User",
        permissions=[
            Permission(PermissionType.VIEW_PORTFOLIO, "View demo portfolio"),
            Permission(PermissionType.RUN_QUICK_ANALYSIS, "Run demo analysis")
        ],
        max_portfolio_value=1000.0,  # $1K demo limit
        max_api_calls_per_day=100
    )
}