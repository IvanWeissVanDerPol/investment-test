"""
Password hashing and validation service using Argon2.
Provides secure password handling for user authentication.
"""

import secrets
import string
from typing import Optional

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, HashingError
    ARGON2_AVAILABLE = True
except ImportError:
    # Fallback to bcrypt if argon2 is not available
    try:
        import bcrypt
        BCRYPT_AVAILABLE = True
    except ImportError:
        BCRYPT_AVAILABLE = False
    ARGON2_AVAILABLE = False

from config.settings import get_settings
from investment_system.core.logging import get_logger
from investment_system.core.exceptions import APIError, ErrorCode

logger = get_logger(__name__)


class PasswordService:
    """
    Service for secure password hashing and verification.
    
    Uses Argon2 (preferred) or bcrypt (fallback) for password hashing.
    Provides password strength validation and secure password generation.
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        if ARGON2_AVAILABLE:
            self.ph = PasswordHasher(
                time_cost=2,        # Number of iterations
                memory_cost=65536,  # Memory usage in KiB (64MB)
                parallelism=1,      # Number of parallel threads
                hash_len=32,        # Hash length
                salt_len=16         # Salt length
            )
            self.backend = "argon2"
        elif BCRYPT_AVAILABLE:
            self.rounds = 12  # bcrypt rounds
            self.backend = "bcrypt"
        else:
            raise RuntimeError("No password hashing backend available. Install argon2-cffi or bcrypt.")
        
        logger.info(f"Password service initialized with {self.backend} backend")
    
    async def hash_password(self, password: str) -> str:
        """
        Hash a password securely.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Raises:
            APIError: If password hashing fails
        """
        try:
            if not password:
                raise APIError(
                    ErrorCode.VALIDATION_ERROR,
                    "Password cannot be empty"
                )
            
            # Validate password strength
            validation_result = self.validate_password_strength(password)
            if not validation_result["is_valid"]:
                raise APIError(
                    ErrorCode.VALIDATION_ERROR,
                    f"Password too weak: {', '.join(validation_result['errors'])}"
                )
            
            if self.backend == "argon2":
                return self.ph.hash(password)
            else:  # bcrypt
                salt = bcrypt.gensalt(rounds=self.rounds)
                return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
        except APIError:
            raise
        except Exception as e:
            logger.error("Password hashing failed", error=str(e))
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                "Password hashing failed"
            ) from e
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            if not password or not hashed_password:
                return False
            
            if self.backend == "argon2":
                try:
                    self.ph.verify(hashed_password, password)
                    return True
                except VerifyMismatchError:
                    return False
            else:  # bcrypt
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    hashed_password.encode('utf-8')
                )
                
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            # Return False instead of raising an exception for security
            return False
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Validate password strength based on security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "score": int (0-100),
                "errors": List[str],
                "suggestions": List[str]
            }
        """
        errors = []
        suggestions = []
        score = 0
        
        if not password:
            return {
                "is_valid": False,
                "score": 0,
                "errors": ["Password cannot be empty"],
                "suggestions": ["Provide a password"]
            }
        
        # Check minimum length
        min_length = self.settings.security.password_min_length
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        else:
            score += 20
        
        # Check for uppercase letters
        if self.settings.security.password_require_uppercase:
            if not any(c.isupper() for c in password):
                errors.append("Password must contain at least one uppercase letter")
            else:
                score += 20
        
        # Check for lowercase letters
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 20
        
        # Check for numbers
        if self.settings.security.password_require_numbers:
            if not any(c.isdigit() for c in password):
                errors.append("Password must contain at least one number")
            else:
                score += 20
        
        # Check for special characters
        if self.settings.security.password_require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")
            else:
                score += 20
        
        # Additional scoring for length
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Check for common patterns
        if password.lower() in ["password", "123456", "qwerty", "admin"]:
            errors.append("Password is too common")
            score = max(0, score - 30)
        
        # Check for repeated characters
        if len(set(password)) < len(password) * 0.6:
            suggestions.append("Avoid repeating characters")
            score = max(0, score - 10)
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            suggestions.append("Avoid sequential characters (e.g., abc, 123)")
            score = max(0, score - 10)
        
        # Generate suggestions
        if errors:
            if len(password) < min_length:
                suggestions.append(f"Make password at least {min_length} characters")
            if not any(c.isupper() for c in password):
                suggestions.append("Add uppercase letters")
            if not any(c.islower() for c in password):
                suggestions.append("Add lowercase letters")
            if not any(c.isdigit() for c in password):
                suggestions.append("Add numbers")
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                suggestions.append("Add special characters")
        
        return {
            "is_valid": len(errors) == 0,
            "score": min(100, score),
            "errors": errors,
            "suggestions": suggestions
        }
    
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure password.
        
        Args:
            length: Length of password to generate
            
        Returns:
            Secure random password
        """
        if length < 8:
            length = 8
        
        # Ensure password meets requirements
        chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Start with required character types
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(special_chars)
        ]
        
        # Fill remaining length with random choices from all character sets
        all_chars = chars + special_chars
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password to randomize character positions
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check if password contains sequential characters."""
        sequences = [
            "abcdefghijklmnopqrstuvwxyz",
            "0123456789",
            "qwertyuiopasdfghjklzxcvbnm"  # QWERTY keyboard layout
        ]
        
        password_lower = password.lower()
        
        for sequence in sequences:
            for i in range(len(sequence) - 2):
                if sequence[i:i+3] in password_lower:
                    return True
                # Check reverse sequences too
                if sequence[i:i+3][::-1] in password_lower:
                    return True
        
        return False
    
    async def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be updated.
        
        Args:
            hashed_password: Existing password hash
            
        Returns:
            True if hash should be updated, False otherwise
        """
        try:
            if self.backend == "argon2":
                return self.ph.check_needs_rehash(hashed_password)
            else:  # bcrypt
                # For bcrypt, we can check if the cost is different
                # This is a simple implementation; in practice you might want more sophisticated logic
                if hashed_password.startswith('$2b$'):
                    cost_part = hashed_password.split('$')[2]
                    current_cost = int(cost_part)
                    return current_cost < self.rounds
                return False
        except Exception as e:
            logger.error("Error checking if password needs rehash", error=str(e))
            return False
    
    def get_password_policy(self) -> dict:
        """
        Get current password policy requirements.
        
        Returns:
            Dictionary with policy requirements
        """
        return {
            "min_length": self.settings.security.password_min_length,
            "require_uppercase": self.settings.security.password_require_uppercase,
            "require_lowercase": True,  # Always required
            "require_numbers": self.settings.security.password_require_numbers,
            "require_special": self.settings.security.password_require_special,
            "backend": self.backend
        }


# Global service instance
_password_service: Optional[PasswordService] = None


def get_password_service() -> PasswordService:
    """Get the global password service instance."""
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service