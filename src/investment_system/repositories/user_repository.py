"""
User repository implementation using the repository pattern.
Handles all database operations for user entities.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from investment_system.repositories.base import AuditableRepository, QueryOptions, QueryFilter
from investment_system.infrastructure.database import User
from investment_system.core.contracts import UserTier
from investment_system.core.exceptions import (
    ResourceNotFoundError, ConflictError, ValidationError
)


class UserRepository(AuditableRepository[User]):
    """
    Repository for user-related database operations.
    
    Provides a clean interface for user data access with proper
    error handling and validation.
    """
    
    async def create(self, user: User) -> User:
        """
        Create a new user account.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user with generated ID and timestamps
            
        Raises:
            ConflictError: If user with email already exists
            ValidationError: If user data is invalid
        """
        # Check if user already exists
        existing = await self.get_by_email(user.email)
        if existing:
            raise ConflictError(
                message=f"User with email '{user.email}' already exists",
                resource_type="user",
                constraint="email_unique"
            )
        
        # Set audit fields
        now = datetime.now(timezone.utc)
        user.created_at = now
        user.updated_at = now
        
        # Implementation will depend on actual database layer
        # This is the interface contract
        pass
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        return await self.find_one_by_field("email", email)
    
    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """
        Get user by API key.
        
        Args:
            api_key: User's API key
            
        Returns:
            User if found, None otherwise
        """
        return await self.find_one_by_field("api_key", api_key)
    
    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated user if found, None otherwise
            
        Raises:
            ValidationError: If update data is invalid
            ConflictError: If email conflicts with existing user
        """
        # Validate email uniqueness if being updated
        if "email" in updates:
            existing = await self.get_by_email(updates["email"])
            if existing and existing.id != user_id:
                raise ConflictError(
                    message=f"Email '{updates['email']}' is already in use",
                    resource_type="user",
                    constraint="email_unique"
                )
        
        # Set updated timestamp
        updates["updated_at"] = datetime.now(timezone.utc)
        
        # Implementation will depend on actual database layer
        pass
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if user was deleted, False if not found
        """
        pass
    
    async def list(self, options: Optional[QueryOptions] = None) -> List[User]:
        """
        List users with optional filtering and pagination.
        
        Args:
            options: Query options for filtering and pagination
            
        Returns:
            List of users matching the criteria
        """
        pass
    
    async def count(self, filters: Optional[List[QueryFilter]] = None) -> int:
        """Count users matching the given filters."""
        pass
    
    async def exists(self, user_id: str) -> bool:
        """Check if user exists by ID."""
        user = await self.get_by_id(user_id)
        return user is not None
    
    async def create_many(self, users: List[User]) -> List[User]:
        """Create multiple users in a single transaction."""
        created_users = []
        for user in users:
            created_user = await self.create(user)
            created_users.append(created_user)
        return created_users
    
    async def update_many(self, updates: List[Dict[str, Any]]) -> List[User]:
        """Update multiple users in a single transaction."""
        updated_users = []
        for update in updates:
            if "id" not in update:
                raise ValidationError("User ID required for bulk update")
            
            user_id = update.pop("id")
            updated_user = await self.update(user_id, update)
            if updated_user:
                updated_users.append(updated_user)
        return updated_users
    
    async def delete_many(self, user_ids: List[str]) -> int:
        """Delete multiple users in a single transaction."""
        deleted_count = 0
        for user_id in user_ids:
            if await self.delete(user_id):
                deleted_count += 1
        return deleted_count
    
    async def find_by_field(self, field: str, value: Any) -> List[User]:
        """Find users by a specific field value."""
        pass
    
    async def find_one_by_field(self, field: str, value: Any) -> Optional[User]:
        """Find a single user by a specific field value."""
        pass
    
    async def get_audit_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get audit history for a user."""
        pass
    
    async def get_created_by_user(self, user_id: str, options: Optional[QueryOptions] = None) -> List[User]:
        """Get users created by a specific user (for admin functionality)."""
        pass
    
    async def get_modified_since(self, since_datetime: str, options: Optional[QueryOptions] = None) -> List[User]:
        """Get users modified since a specific datetime."""
        pass
    
    # User-specific methods
    
    async def get_by_tier(self, tier: UserTier, options: Optional[QueryOptions] = None) -> List[User]:
        """
        Get users by subscription tier.
        
        Args:
            tier: User subscription tier
            options: Query options for filtering and pagination
            
        Returns:
            List of users with the specified tier
        """
        return await self.find_by_field("tier", tier.value)
    
    async def get_active_users(self, options: Optional[QueryOptions] = None) -> List[User]:
        """
        Get all active (non-suspended) users.
        
        Args:
            options: Query options for filtering and pagination
            
        Returns:
            List of active users
        """
        filters = [QueryFilter(field="is_active", operator="eq", value=True)]
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.list(options)
    
    async def get_users_by_registration_date(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        options: Optional[QueryOptions] = None
    ) -> List[User]:
        """
        Get users registered within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range (defaults to now)
            options: Query options for filtering and pagination
            
        Returns:
            List of users registered in the date range
        """
        filters = [
            QueryFilter(field="created_at", operator="ge", value=start_date.isoformat())
        ]
        
        if end_date:
            filters.append(
                QueryFilter(field="created_at", operator="le", value=end_date.isoformat())
            )
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.list(options)
    
    async def update_last_login(self, user_id: str, login_time: Optional[datetime] = None) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User's unique identifier
            login_time: Login timestamp (defaults to now)
            
        Returns:
            Updated user if found, None otherwise
        """
        if login_time is None:
            login_time = datetime.now(timezone.utc)
        
        return await self.update(user_id, {"last_login_at": login_time})
    
    async def update_tier(self, user_id: str, new_tier: UserTier) -> Optional[User]:
        """
        Update user's subscription tier.
        
        Args:
            user_id: User's unique identifier
            new_tier: New subscription tier
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.update(user_id, {
            "tier": new_tier,
            "tier_updated_at": datetime.now(timezone.utc)
        })
    
    async def suspend_user(self, user_id: str, reason: str) -> Optional[User]:
        """
        Suspend a user account.
        
        Args:
            user_id: User's unique identifier
            reason: Reason for suspension
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.update(user_id, {
            "is_active": False,
            "suspended_at": datetime.now(timezone.utc),
            "suspension_reason": reason
        })
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a suspended user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.update(user_id, {
            "is_active": True,
            "suspended_at": None,
            "suspension_reason": None
        })
    
    async def verify_email(self, user_id: str) -> Optional[User]:
        """
        Mark user's email as verified.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.update(user_id, {
            "email_verified": True,
            "email_verified_at": datetime.now(timezone.utc)
        })
    
    async def regenerate_api_key(self, user_id: str, new_api_key: str) -> Optional[User]:
        """
        Regenerate user's API key.
        
        Args:
            user_id: User's unique identifier
            new_api_key: New API key to set
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.update(user_id, {
            "api_key": new_api_key,
            "api_key_generated_at": datetime.now(timezone.utc)
        })