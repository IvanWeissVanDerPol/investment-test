"""
User service layer for handling user-related business logic.
Separates business rules from API handlers and data access.
"""

import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from investment_system.services.base import (
    CRUDService, ServiceResult, PaginatedResult,
    ValidationMixin, AuthorizationMixin
)
from investment_system.repositories.user_repository import UserRepository
from investment_system.models.user import User, UserTier
from investment_system.core.exceptions import (
    APIError, ErrorCode, ValidationError, ConflictError,
    AuthenticationError, AuthorizationError
)


class UserService(CRUDService[User], ValidationMixin, AuthorizationMixin):
    """
    Service for user-related business operations.
    
    Handles user registration, authentication, profile management,
    and subscription tier management with proper validation and
    business rule enforcement.
    """
    
    def __init__(self, user_repository: UserRepository, password_service: 'PasswordService'):
        super().__init__()
        self.user_repository = user_repository
        self.password_service = password_service
    
    async def register_user(
        self,
        email: str,
        password: str,
        tier: UserTier = UserTier.FREE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceResult:
        """
        Register a new user account.
        
        Args:
            email: User's email address
            password: User's password
            tier: Initial subscription tier
            metadata: Additional registration metadata
            
        Returns:
            ServiceResult containing created user or error
        """
        self.log_operation("register_user", metadata={"email": email, "tier": tier.value})
        
        try:
            # Validate input
            validation_result = await self._validate_registration_data(email, password)
            if not validation_result.success:
                return validation_result
            
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                return ServiceResult.error_result(
                    error="User with this email already exists",
                    error_code="USER_ALREADY_EXISTS"
                )
            
            # Hash password
            password_hash = await self.password_service.hash_password(password)
            
            # Generate API key
            api_key = self._generate_api_key()
            
            # Create user entity
            user = User(
                email=email,
                password_hash=password_hash,
                tier=tier,
                api_key=api_key,
                is_active=True,
                email_verified=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save to repository
            created_user = await self.user_repository.create(user)
            
            self.log_operation(
                "register_user",
                user_id=created_user.id,
                success=True,
                metadata={"tier": tier.value}
            )
            
            # Don't return password hash in response
            user_data = self._sanitize_user_data(created_user)
            
            return ServiceResult.success_result(
                data=user_data,
                metadata={"message": "User registered successfully"}
            )
            
        except Exception as e:
            self.log_operation(
                "register_user",
                success=False,
                error=str(e),
                metadata={"email": email}
            )
            
            return ServiceResult.error_result(
                error=f"User registration failed: {str(e)}",
                error_code="REGISTRATION_FAILED"
            )
    
    async def authenticate_user(self, email: str, password: str) -> ServiceResult:
        """
        Authenticate user credentials.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            ServiceResult containing user data or error
        """
        self.log_operation("authenticate_user", metadata={"email": email})
        
        try:
            # Get user by email
            user = await self.user_repository.get_by_email(email)
            if not user:
                return ServiceResult.error_result(
                    error="Invalid email or password",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # Check if user is active
            if not user.is_active:
                return ServiceResult.error_result(
                    error="User account is suspended",
                    error_code="ACCOUNT_SUSPENDED"
                )
            
            # Verify password
            password_valid = await self.password_service.verify_password(password, user.password_hash)
            if not password_valid:
                return ServiceResult.error_result(
                    error="Invalid email or password",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # Update last login
            await self.user_repository.update_last_login(user.id)
            
            self.log_operation(
                "authenticate_user",
                user_id=user.id,
                success=True
            )
            
            # Don't return password hash in response
            user_data = self._sanitize_user_data(user)
            
            return ServiceResult.success_result(
                data=user_data,
                metadata={"message": "Authentication successful"}
            )
            
        except Exception as e:
            self.log_operation(
                "authenticate_user",
                success=False,
                error=str(e),
                metadata={"email": email}
            )
            
            return ServiceResult.error_result(
                error=f"Authentication failed: {str(e)}",
                error_code="AUTHENTICATION_FAILED"
            )
    
    async def get_user_by_api_key(self, api_key: str) -> ServiceResult:
        """
        Get user by API key for API authentication.
        
        Args:
            api_key: User's API key
            
        Returns:
            ServiceResult containing user data or error
        """
        try:
            user = await self.user_repository.get_by_api_key(api_key)
            if not user:
                return ServiceResult.error_result(
                    error="Invalid API key",
                    error_code="INVALID_API_KEY"
                )
            
            if not user.is_active:
                return ServiceResult.error_result(
                    error="User account is suspended",
                    error_code="ACCOUNT_SUSPENDED"
                )
            
            user_data = self._sanitize_user_data(user)
            return ServiceResult.success_result(data=user_data)
            
        except Exception as e:
            return ServiceResult.error_result(
                error=f"API key validation failed: {str(e)}",
                error_code="API_KEY_VALIDATION_FAILED"
            )
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
        requesting_user_id: str
    ) -> ServiceResult:
        """
        Update user profile information.
        
        Args:
            user_id: ID of user to update
            updates: Profile updates
            requesting_user_id: ID of user making the request
            
        Returns:
            ServiceResult containing updated user or error
        """
        # Check authorization
        auth_result = await self.require_user_access(requesting_user_id, user_id, "update profile")
        if not auth_result.success:
            return auth_result
        
        # Validate updates
        allowed_fields = {
            "email", "first_name", "last_name", "timezone", 
            "notification_preferences", "trading_preferences"
        }
        
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            return ServiceResult.error_result(
                error=f"Invalid fields for profile update: {', '.join(invalid_fields)}",
                error_code="INVALID_PROFILE_FIELDS"
            )
        
        # Validate email if being updated
        if "email" in updates:
            email_validation = self.validate_email(updates["email"])
            if not email_validation.success:
                return email_validation
        
        try:
            updated_user = await self.user_repository.update(user_id, updates)
            if not updated_user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            self.log_operation(
                "update_user_profile",
                user_id=user_id,
                success=True,
                metadata={"updated_fields": list(updates.keys())}
            )
            
            user_data = self._sanitize_user_data(updated_user)
            return ServiceResult.success_result(data=user_data)
            
        except Exception as e:
            self.log_operation(
                "update_user_profile",
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            return ServiceResult.error_result(
                error=f"Profile update failed: {str(e)}",
                error_code="PROFILE_UPDATE_FAILED"
            )
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        requesting_user_id: str
    ) -> ServiceResult:
        """
        Change user password.
        
        Args:
            user_id: ID of user changing password
            current_password: Current password for verification
            new_password: New password
            requesting_user_id: ID of user making the request
            
        Returns:
            ServiceResult indicating success or failure
        """
        # Check authorization
        auth_result = await self.require_user_access(requesting_user_id, user_id, "change password")
        if not auth_result.success:
            return auth_result
        
        # Validate new password
        password_validation = await self._validate_password(new_password)
        if not password_validation.success:
            return password_validation
        
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            # Verify current password
            password_valid = await self.password_service.verify_password(current_password, user.password_hash)
            if not password_valid:
                return ServiceResult.error_result(
                    error="Current password is incorrect",
                    error_code="INVALID_CURRENT_PASSWORD"
                )
            
            # Hash new password
            new_password_hash = await self.password_service.hash_password(new_password)
            
            # Update password
            await self.user_repository.update(user_id, {
                "password_hash": new_password_hash,
                "password_changed_at": datetime.now(timezone.utc)
            })
            
            self.log_operation("change_password", user_id=user_id, success=True)
            
            return ServiceResult.success_result(
                metadata={"message": "Password changed successfully"}
            )
            
        except Exception as e:
            self.log_operation(
                "change_password",
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            return ServiceResult.error_result(
                error=f"Password change failed: {str(e)}",
                error_code="PASSWORD_CHANGE_FAILED"
            )
    
    async def upgrade_user_tier(
        self,
        user_id: str,
        new_tier: UserTier,
        requesting_user_id: str
    ) -> ServiceResult:
        """
        Upgrade user's subscription tier.
        
        Args:
            user_id: ID of user to upgrade
            new_tier: New subscription tier
            requesting_user_id: ID of user making the request
            
        Returns:
            ServiceResult containing updated user or error
        """
        # For now, only allow users to upgrade their own accounts
        auth_result = await self.require_user_access(requesting_user_id, user_id, "upgrade tier")
        if not auth_result.success:
            return auth_result
        
        try:
            # Get current user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            # Validate upgrade (no downgrades for now)
            tier_hierarchy = {
                UserTier.FREE: 0,
                UserTier.STARTER: 1,
                UserTier.PRO: 2
            }
            
            if tier_hierarchy[new_tier] < tier_hierarchy[user.tier]:
                return ServiceResult.error_result(
                    error="Tier downgrades not supported. Contact support.",
                    error_code="TIER_DOWNGRADE_NOT_SUPPORTED"
                )
            
            if new_tier == user.tier:
                return ServiceResult.error_result(
                    error="User already has this tier",
                    error_code="TIER_ALREADY_CURRENT"
                )
            
            # Update tier
            updated_user = await self.user_repository.update_tier(user_id, new_tier)
            
            self.log_operation(
                "upgrade_user_tier",
                user_id=user_id,
                success=True,
                metadata={"old_tier": user.tier.value, "new_tier": new_tier.value}
            )
            
            user_data = self._sanitize_user_data(updated_user)
            return ServiceResult.success_result(
                data=user_data,
                metadata={"message": f"Tier upgraded to {new_tier.value}"}
            )
            
        except Exception as e:
            self.log_operation(
                "upgrade_user_tier",
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            return ServiceResult.error_result(
                error=f"Tier upgrade failed: {str(e)}",
                error_code="TIER_UPGRADE_FAILED"
            )
    
    async def regenerate_api_key(self, user_id: str, requesting_user_id: str) -> ServiceResult:
        """
        Regenerate user's API key.
        
        Args:
            user_id: ID of user to regenerate key for
            requesting_user_id: ID of user making the request
            
        Returns:
            ServiceResult containing new API key or error
        """
        # Check authorization
        auth_result = await self.require_user_access(requesting_user_id, user_id, "regenerate API key")
        if not auth_result.success:
            return auth_result
        
        try:
            # Generate new API key
            new_api_key = self._generate_api_key()
            
            # Update user
            updated_user = await self.user_repository.regenerate_api_key(user_id, new_api_key)
            if not updated_user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            self.log_operation("regenerate_api_key", user_id=user_id, success=True)
            
            return ServiceResult.success_result(
                data={"api_key": new_api_key},
                metadata={"message": "API key regenerated successfully"}
            )
            
        except Exception as e:
            self.log_operation(
                "regenerate_api_key",
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            return ServiceResult.error_result(
                error=f"API key regeneration failed: {str(e)}",
                error_code="API_KEY_REGENERATION_FAILED"
            )
    
    # CRUD interface implementations
    
    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> ServiceResult:
        """Create user via CRUD interface."""
        return await self.register_user(
            email=data.get("email"),
            password=data.get("password"),
            tier=UserTier(data.get("tier", "free"))
        )
    
    async def get_by_id(self, entity_id: str, user_id: Optional[str] = None) -> ServiceResult:
        """Get user by ID via CRUD interface."""
        try:
            user = await self.user_repository.get_by_id(entity_id)
            if not user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            user_data = self._sanitize_user_data(user)
            return ServiceResult.success_result(data=user_data)
            
        except Exception as e:
            return ServiceResult.error_result(
                error=f"Failed to get user: {str(e)}",
                error_code="GET_USER_FAILED"
            )
    
    async def update(self, entity_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> ServiceResult:
        """Update user via CRUD interface."""
        return await self.update_user_profile(entity_id, updates, user_id or entity_id)
    
    async def delete(self, entity_id: str, user_id: Optional[str] = None) -> ServiceResult:
        """Delete user via CRUD interface (suspend for now)."""
        try:
            updated_user = await self.user_repository.suspend_user(
                entity_id, 
                "Account deleted by user request"
            )
            
            if not updated_user:
                return ServiceResult.error_result(
                    error="User not found",
                    error_code="USER_NOT_FOUND"
                )
            
            return ServiceResult.success_result(
                metadata={"message": "User account suspended"}
            )
            
        except Exception as e:
            return ServiceResult.error_result(
                error=f"Failed to delete user: {str(e)}",
                error_code="DELETE_USER_FAILED"
            )
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        user_id: Optional[str] = None
    ) -> ServiceResult:
        """List users via CRUD interface (admin only)."""
        # This would require admin authorization
        return ServiceResult.error_result(
            error="User listing requires admin privileges",
            error_code="ADMIN_REQUIRED"
        )
    
    # Helper methods
    
    async def _validate_registration_data(self, email: str, password: str) -> ServiceResult:
        """Validate user registration data."""
        # Validate required fields
        if not email or not password:
            return ServiceResult.error_result(
                error="Email and password are required",
                error_code="MISSING_REQUIRED_FIELDS"
            )
        
        # Validate email format
        email_validation = self.validate_email(email)
        if not email_validation.success:
            return email_validation
        
        # Validate password
        password_validation = await self._validate_password(password)
        if not password_validation.success:
            return password_validation
        
        return ServiceResult.success_result()
    
    async def _validate_password(self, password: str) -> ServiceResult:
        """Validate password strength."""
        # Basic password validation
        if len(password) < 8:
            return ServiceResult.error_result(
                error="Password must be at least 8 characters long",
                error_code="PASSWORD_TOO_SHORT"
            )
        
        # Add more password strength checks as needed
        # - uppercase, lowercase, numbers, special characters
        
        return ServiceResult.success_result()
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        return f"inv_{secrets.token_urlsafe(32)}"
    
    def _sanitize_user_data(self, user: User) -> Dict[str, Any]:
        """Remove sensitive fields from user data."""
        user_dict = user.to_dict() if hasattr(user, 'to_dict') else user.__dict__.copy()
        
        # Remove sensitive fields
        sensitive_fields = {
            "password_hash", "suspension_reason", "internal_notes"
        }
        
        for field in sensitive_fields:
            user_dict.pop(field, None)
        
        return user_dict