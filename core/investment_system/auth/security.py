"""
Security utilities for password hashing, encryption, and security validation
"""

import hashlib
import secrets
import base64
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import bcrypt
import jwt
from cryptography.fernet import Fernet
import pyotp
import qrcode
from io import BytesIO

from ..utils.secure_config_manager import get_config_manager


class SecurityManager:
    """
    Manages all security-related operations including password hashing,
    JWT tokens, MFA, and encryption
    """
    
    def __init__(self):
        """Initialize security manager"""
        self.config = get_config_manager()
        self.security_config = self.config.get_security_config()
        
        # Initialize encryption
        self._cipher_suite = None
        if self.security_config.encryption_key:
            try:
                key_bytes = base64.urlsafe_b64decode(self.security_config.encryption_key.encode())
                self._cipher_suite = Fernet(base64.urlsafe_b64encode(key_bytes))
            except Exception:
                self._cipher_suite = None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength
        Returns dict with validation results and suggestions
        """
        validation = {
            'is_valid': True,
            'score': 0,
            'issues': [],
            'suggestions': []
        }
        
        # Length check
        if len(password) < 12:
            validation['is_valid'] = False
            validation['issues'].append('Password must be at least 12 characters long')
            validation['suggestions'].append('Use a longer password (12+ characters)')
        else:
            validation['score'] += 20
        
        # Character variety checks
        if not re.search(r'[a-z]', password):
            validation['is_valid'] = False
            validation['issues'].append('Password must contain lowercase letters')
            validation['suggestions'].append('Add lowercase letters (a-z)')
        else:
            validation['score'] += 15
        
        if not re.search(r'[A-Z]', password):
            validation['is_valid'] = False
            validation['issues'].append('Password must contain uppercase letters')
            validation['suggestions'].append('Add uppercase letters (A-Z)')
        else:
            validation['score'] += 15
        
        if not re.search(r'\d', password):
            validation['is_valid'] = False
            validation['issues'].append('Password must contain numbers')
            validation['suggestions'].append('Add numbers (0-9)')
        else:
            validation['score'] += 15
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            validation['is_valid'] = False
            validation['issues'].append('Password must contain special characters')
            validation['suggestions'].append('Add special characters (!@#$%^&*)')
        else:
            validation['score'] += 15
        
        # Common password patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'admin', r'letmein',
            r'welcome', r'monkey', r'dragon', r'master', r'iloveyou'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                validation['is_valid'] = False
                validation['issues'].append('Password contains common patterns')
                validation['suggestions'].append('Avoid common words and patterns')
                break
        else:
            validation['score'] += 10
        
        # Repetition check
        if re.search(r'(.)\1{2,}', password):
            validation['issues'].append('Avoid repeating characters')
            validation['suggestions'].append('Reduce character repetition')
        else:
            validation['score'] += 10
        
        return validation
    
    def generate_jwt_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'iat': datetime.now(),
            'exp': datetime.now() + timedelta(seconds=self.security_config.session_timeout),
            'iss': 'InvestmentAI'
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(
            payload,
            self.security_config.jwt_secret,
            algorithm='HS256'
        )
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.security_config.jwt_secret,
                algorithms=['HS256'],
                issuer='InvestmentAI'
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self._cipher_suite:
            return None
        
        try:
            encrypted_bytes = self._cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception:
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self._cipher_suite:
            return None
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            return None
    
    def generate_mfa_secret(self) -> str:
        """Generate MFA secret for TOTP"""
        return pyotp.random_base32()
    
    def generate_mfa_qr_code(self, user_email: str, mfa_secret: str) -> bytes:
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
            name=user_email,
            issuer_name="InvestmentAI"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        qr_image.save(img_buffer, format='PNG')
        return img_buffer.getvalue()
    
    def verify_mfa_token(self, mfa_secret: str, token: str) -> bool:
        """Verify MFA TOTP token"""
        try:
            totp = pyotp.TOTP(mfa_secret)
            return totp.verify(token, valid_window=1)  # Allow 30 seconds window
        except Exception:
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_username(self, username: str) -> Dict[str, Any]:
        """Validate username"""
        validation = {
            'is_valid': True,
            'issues': []
        }
        
        if len(username) < 3:
            validation['is_valid'] = False
            validation['issues'].append('Username must be at least 3 characters long')
        
        if len(username) > 30:
            validation['is_valid'] = False
            validation['issues'].append('Username must be less than 30 characters')
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            validation['is_valid'] = False
            validation['issues'].append('Username can only contain letters, numbers, hyphens, and underscores')
        
        return validation
    
    def get_password_reset_token(self, user_id: str) -> Tuple[str, datetime]:
        """Generate password reset token"""
        token = self.generate_secure_token(48)
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry
        
        # Store token hash for verification
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        return token, expires_at
    
    def verify_password_reset_token(self, token: str, stored_hash: str, expires_at: datetime) -> bool:
        """Verify password reset token"""
        if datetime.now() > expires_at:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return secrets.compare_digest(token_hash, stored_hash)


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def hash_password(password: str) -> str:
    """Convenience function to hash password"""
    return get_security_manager().hash_password(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Convenience function to verify password"""
    return get_security_manager().verify_password(password, password_hash)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Convenience function to validate password strength"""
    return get_security_manager().validate_password_strength(password)