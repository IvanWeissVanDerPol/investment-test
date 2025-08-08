"""
Authentication Manager
Handles user authentication, session management, and authorization
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, jsonify, g
import sqlite3
import json

from .models import User, RoleType, PermissionType
from .security import SecurityManager, get_security_manager
from ..utils.secure_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages user authentication, authorization, and session management
    """
    
    def __init__(self, db_path: str = None):
        """Initialize authentication manager"""
        self.config = get_config_manager()
        self.security = get_security_manager()
        
        # Database setup
        self.db_path = db_path or "core/database/investment_system.db"
        self._initialize_auth_tables()
        
        # Session settings
        self.session_timeout = self.config.get_security_config().session_timeout
    
    def _initialize_auth_tables(self):
        """Initialize authentication database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        email_verified BOOLEAN DEFAULT FALSE,
                        phone_verified BOOLEAN DEFAULT FALSE,
                        mfa_enabled BOOLEAN DEFAULT FALSE,
                        mfa_secret TEXT,
                        role TEXT DEFAULT 'basic',
                        permissions TEXT, -- JSON array
                        last_login TIMESTAMP,
                        last_activity TIMESTAMP,
                        failed_login_attempts INTEGER DEFAULT 0,
                        account_locked_until TIMESTAMP,
                        portfolio_balance REAL DEFAULT 900.0,
                        risk_tolerance TEXT DEFAULT 'medium',
                        investment_goals TEXT, -- JSON array
                        subscription_tier TEXT DEFAULT 'basic',
                        subscription_expires TIMESTAMP,
                        api_calls_used_today INTEGER DEFAULT 0,
                        api_calls_limit INTEGER DEFAULT 1000,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        jwt_token TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        token_hash TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
                """)
                
                # Create default admin user if none exists
                self._create_default_admin_if_needed(conn)
                
        except Exception as e:
            logger.error(f"Failed to initialize auth tables: {e}")
            raise
    
    def _create_default_admin_if_needed(self, conn):
        """Create default admin user if no users exist"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create default admin user
            admin_user = User(
                email="admin@investmentai.com",
                username="admin",
                first_name="Admin",
                last_name="User",
                role=RoleType.ADMIN,
                is_verified=True,
                email_verified=True
            )
            
            # Set default password (should be changed on first login)
            default_password = "ChangeMe123!@#"
            admin_user.password_hash = self.security.hash_password(default_password)
            
            self._save_user_to_db(conn, admin_user)
            logger.info("Created default admin user - email: admin@investmentai.com, password: ChangeMe123!@#")
    
    def _save_user_to_db(self, conn, user: User):
        """Save user to database"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (
                user_id, email, username, password_hash, first_name, last_name,
                is_active, is_verified, email_verified, phone_verified,
                mfa_enabled, mfa_secret, role, permissions,
                last_login, last_activity, failed_login_attempts, account_locked_until,
                portfolio_balance, risk_tolerance, investment_goals,
                subscription_tier, subscription_expires, api_calls_used_today, api_calls_limit,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.email, user.username, user.password_hash,
            user.first_name, user.last_name, user.is_active, user.is_verified,
            user.email_verified, user.phone_verified, user.mfa_enabled, user.mfa_secret,
            user.role.value, json.dumps([p.value for p in user.permissions]),
            user.last_login, user.last_activity, user.failed_login_attempts, user.account_locked_until,
            user.portfolio_balance, user.risk_tolerance, json.dumps(user.investment_goals),
            user.subscription_tier, user.subscription_expires, user.api_calls_used_today, user.api_calls_limit,
            user.created_at, user.updated_at
        ))
        conn.commit()
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: str = "", last_name: str = "", 
                   role: RoleType = RoleType.BASIC) -> Optional[User]:
        """Create a new user"""
        
        # Validate input
        if not self.security.validate_email(email):
            raise ValueError("Invalid email format")
        
        username_validation = self.security.validate_username(username)
        if not username_validation['is_valid']:
            raise ValueError(f"Invalid username: {', '.join(username_validation['issues'])}")
        
        password_validation = self.security.validate_password_strength(password)
        if not password_validation['is_valid']:
            raise ValueError(f"Weak password: {', '.join(password_validation['issues'])}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if user already exists
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE email = ? OR username = ?", (email, username))
                if cursor.fetchone():
                    raise ValueError("User with this email or username already exists")
                
                # Create new user
                user = User(
                    email=email,
                    username=username,
                    password_hash=self.security.hash_password(password),
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                
                self._save_user_to_db(conn, user)
                logger.info(f"Created new user: {email}")
                return user
                
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            raise
    
    def authenticate_user(self, email_or_username: str, password: str, 
                         ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate user and create session"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Find user
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE (email = ? OR username = ?) AND is_active = TRUE
                """, (email_or_username, email_or_username))
                
                user_row = cursor.fetchone()
                if not user_row:
                    logger.warning(f"Authentication failed: user not found - {email_or_username}")
                    return None
                
                user = self._row_to_user(user_row)
                
                # Check if account is locked
                if user.is_account_locked():
                    logger.warning(f"Authentication failed: account locked - {email_or_username}")
                    return None
                
                # Verify password
                if not self.security.verify_password(password, user.password_hash):
                    # Increment failed attempts
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.lock_account(30)  # Lock for 30 minutes
                        logger.warning(f"Account locked due to failed attempts - {email_or_username}")
                    
                    user.updated_at = datetime.now()
                    self._save_user_to_db(conn, user)
                    return None
                
                # Successful authentication
                user.failed_login_attempts = 0
                user.last_login = datetime.now()
                user.last_activity = datetime.now()
                user.updated_at = datetime.now()
                self._save_user_to_db(conn, user)
                
                # Create session
                session_data = self._create_user_session(conn, user, ip_address, user_agent)
                
                logger.info(f"User authenticated successfully: {email_or_username}")
                return {
                    'user': user.to_dict(),
                    'session': session_data
                }
                
        except Exception as e:
            logger.error(f"Authentication error for {email_or_username}: {e}")
            return None
    
    def _create_user_session(self, conn, user: User, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Create user session and JWT token"""
        
        # Generate JWT token
        jwt_token = self.security.generate_jwt_token(
            user.user_id,
            additional_claims={
                'role': user.role.value,
                'permissions': [p.value for p in user.permissions]
            }
        )
        
        # Create session record
        session_id = self.security.generate_secure_token()
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (session_id, user_id, jwt_token, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user.user_id, jwt_token, ip_address, user_agent, expires_at))
        
        conn.commit()
        
        return {
            'session_id': session_id,
            'jwt_token': jwt_token,
            'expires_at': expires_at.isoformat()
        }
    
    def verify_session(self, jwt_token: str) -> Optional[User]:
        """Verify user session and return user"""
        
        # Verify JWT token
        payload = self.security.verify_jwt_token(jwt_token)
        if not payload:
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check session in database
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, u.* FROM user_sessions s
                    JOIN users u ON s.user_id = u.user_id
                    WHERE s.jwt_token = ? AND s.is_active = TRUE AND s.expires_at > ?
                """, (jwt_token, datetime.now()))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Extract user data (session columns + user columns)
                user_data = row[8:]  # Skip session columns
                user = self._row_to_user(user_data)
                
                # Update last activity
                user.update_last_activity()
                self._save_user_to_db(conn, user)
                
                return user
                
        except Exception as e:
            logger.error(f"Session verification error: {e}")
            return None
    
    def logout_user(self, jwt_token: str):
        """Logout user by invalidating session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE jwt_token = ?
                """, (jwt_token,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ? AND is_active = TRUE", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        # Map database columns to User fields
        user_data = {
            'user_id': row[0],
            'email': row[1],
            'username': row[2],
            'password_hash': row[3],
            'first_name': row[4] or "",
            'last_name': row[5] or "",
            'is_active': bool(row[6]),
            'is_verified': bool(row[7]),
            'email_verified': bool(row[8]),
            'phone_verified': bool(row[9]),
            'mfa_enabled': bool(row[10]),
            'mfa_secret': row[11],
            'role': RoleType(row[12]),
            'permissions': [PermissionType(p) for p in json.loads(row[13] or '[]')],
            'portfolio_balance': row[18] or 900.0,
            'risk_tolerance': row[19] or 'medium',
            'investment_goals': json.loads(row[20] or '["AI/robotics growth"]'),
            'subscription_tier': row[21] or 'basic',
            'api_calls_used_today': row[23] or 0,
            'api_calls_limit': row[24] or 1000
        }
        
        # Handle datetime fields
        datetime_fields = [
            ('last_login', 14),
            ('last_activity', 15),
            ('account_locked_until', 17),
            ('subscription_expires', 22),
            ('created_at', 25),
            ('updated_at', 26)
        ]
        
        for field_name, index in datetime_fields:
            if row[index]:
                user_data[field_name] = datetime.fromisoformat(row[index])
        
        user_data['failed_login_attempts'] = row[16] or 0
        
        return User(**user_data)


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# Flask decorators for authentication and authorization
def login_required(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get JWT token from Authorization header or session
        auth_header = request.headers.get('Authorization')
        jwt_token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            jwt_token = auth_header[7:]
        elif 'jwt_token' in session:
            jwt_token = session['jwt_token']
        
        if not jwt_token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify session
        auth_manager = get_auth_manager()
        user = auth_manager.verify_session(jwt_token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Add user to Flask g object
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission: PermissionType):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user.has_permission(permission):
                return jsonify({'error': f'Permission required: {permission.value}'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator