"""
Abstract base classes for the repository pattern.
Provides clean separation between business logic and data access.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class QueryFilter:
    """Generic filter for database queries."""
    field: str
    operator: str  # eq, ne, lt, le, gt, ge, in, like, etc.
    value: Any


@dataclass
class QueryOptions:
    """Query options for pagination, sorting, etc."""
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[str] = None
    order_direction: str = "asc"  # asc or desc
    filters: List[QueryFilter] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []


class Repository(ABC, Generic[T]):
    """
    Abstract base repository providing common database operations.
    
    All repositories should inherit from this class to ensure
    consistent interface across the data access layer.
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the database.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with any generated fields (ID, timestamps)
            
        Raises:
            ConflictError: If entity already exists
            ValidationError: If entity data is invalid
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity by ID.
        
        Args:
            entity_id: The unique identifier
            updates: Dictionary of field updates
            
        Returns:
            The updated entity if found, None otherwise
            
        Raises:
            ValidationError: If update data is invalid
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def list(self, options: Optional[QueryOptions] = None) -> List[T]:
        """
        List entities with optional filtering, pagination, and sorting.
        
        Args:
            options: Query options for filtering and pagination
            
        Returns:
            List of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[List[QueryFilter]] = None) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            filters: Optional list of filters to apply
            
        Returns:
            Number of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity exists, False otherwise
        """
        pass


class TransactionalRepository(Repository[T]):
    """
    Extended repository interface for transactional operations.
    
    Provides support for batch operations and transactions.
    """
    
    @abstractmethod
    async def create_many(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in a single transaction.
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of created entities with generated fields
            
        Raises:
            ValidationError: If any entity data is invalid
            ConflictError: If any entity conflicts with existing data
        """
        pass
    
    @abstractmethod
    async def update_many(self, updates: List[Dict[str, Any]]) -> List[T]:
        """
        Update multiple entities in a single transaction.
        
        Args:
            updates: List of update dictionaries, each must contain 'id'
            
        Returns:
            List of updated entities
            
        Raises:
            ValidationError: If any update data is invalid
        """
        pass
    
    @abstractmethod
    async def delete_many(self, entity_ids: List[str]) -> int:
        """
        Delete multiple entities in a single transaction.
        
        Args:
            entity_ids: List of entity IDs to delete
            
        Returns:
            Number of entities actually deleted
        """
        pass
    
    @abstractmethod
    async def find_by_field(self, field: str, value: Any) -> List[T]:
        """
        Find entities by a specific field value.
        
        Args:
            field: Field name to search by
            value: Value to match
            
        Returns:
            List of matching entities
        """
        pass
    
    @abstractmethod
    async def find_one_by_field(self, field: str, value: Any) -> Optional[T]:
        """
        Find a single entity by a specific field value.
        
        Args:
            field: Field name to search by
            value: Value to match
            
        Returns:
            The first matching entity or None
        """
        pass


class AuditableRepository(TransactionalRepository[T]):
    """
    Repository interface for auditable entities.
    
    Provides operations for entities that track creation/modification metadata.
    """
    
    @abstractmethod
    async def get_audit_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get audit history for an entity.
        
        Args:
            entity_id: The entity identifier
            
        Returns:
            List of audit records showing entity changes over time
        """
        pass
    
    @abstractmethod
    async def get_created_by_user(self, user_id: str, options: Optional[QueryOptions] = None) -> List[T]:
        """
        Get entities created by a specific user.
        
        Args:
            user_id: User identifier
            options: Query options for filtering and pagination
            
        Returns:
            List of entities created by the user
        """
        pass
    
    @abstractmethod
    async def get_modified_since(self, since_datetime: str, options: Optional[QueryOptions] = None) -> List[T]:
        """
        Get entities modified since a specific datetime.
        
        Args:
            since_datetime: ISO datetime string
            options: Query options for filtering and pagination
            
        Returns:
            List of entities modified since the specified time
        """
        pass


# Utility functions for repository implementations

def build_query_filter(field: str, operator: str, value: Any) -> QueryFilter:
    """
    Helper function to build a query filter.
    
    Args:
        field: Field name to filter on
        operator: Comparison operator (eq, ne, lt, le, gt, ge, in, like)
        value: Value to compare against
        
    Returns:
        QueryFilter instance
    """
    return QueryFilter(field=field, operator=operator, value=value)


def build_query_options(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: str = "asc",
    **filters
) -> QueryOptions:
    """
    Helper function to build query options with filters.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by
        order_direction: Order direction (asc/desc)
        **filters: Field filters as keyword arguments
        
    Returns:
        QueryOptions instance
        
    Example:
        options = build_query_options(
            limit=10,
            order_by="created_at",
            status="active",
            user_id="123"
        )
    """
    query_filters = [
        QueryFilter(field=field, operator="eq", value=value)
        for field, value in filters.items()
    ]
    
    return QueryOptions(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        filters=query_filters
    )