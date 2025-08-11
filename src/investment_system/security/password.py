"""
Secure password hashing and token generation.
Enterprise-grade security using Argon2.
"""

from passlib.context import CryptContext
import secrets
from typing import Optional

# Configure password context with Argon2 as primary
# Bcrypt as fallback for compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    argon2__rounds=4,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
    argon2__hash_len=32,
    argon2__salt_len=16,
    bcrypt__rounds=12,
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    Hash password using Argon2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure token.
    
    Args:
        length: Token length (default 32)
        
    Returns:
        URL-safe token string
    """
    if length < 16:
        raise ValueError("Token length must be at least 16")
    return secrets.token_urlsafe(length)


def generate_api_key() -> tuple[str, str]:
    """
    Generate API key pair (key_id, secret_key).
    
    Returns:
        Tuple of (key_id, secret_key)
    """
    key_id = f"ik_{secrets.token_urlsafe(16)}"
    secret_key = f"sk_{secrets.token_urlsafe(32)}"
    return key_id, secret_key


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    Uses same context as passwords for consistency.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify API key against hash.
    
    Args:
        plain_key: Plain API key
        hashed_key: Stored API key hash
        
    Returns:
        True if key matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_key, hashed_key)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if password hash needs to be updated.
    Useful for migrating from older hash schemes.
    
    Args:
        hashed_password: Current password hash
        
    Returns:
        True if rehashing is recommended
    """
    return pwd_context.needs_update(hashed_password)


def generate_temp_password(length: int = 12) -> str:
    """
    Generate temporary password for resets.
    
    Args:
        length: Password length (default 12)
        
    Returns:
        Temporary password string
    """
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password