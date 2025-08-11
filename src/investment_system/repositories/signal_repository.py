"""
Signal repository implementation for trading signals data access.
Handles all database operations for signal entities.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from investment_system.repositories.base import AuditableRepository, QueryOptions, QueryFilter
from investment_system.infrastructure.database import Signal
from investment_system.core.contracts import SignalType
from investment_system.core.exceptions import ValidationError


class SignalRepository(AuditableRepository[Signal]):
    """
    Repository for trading signal database operations.
    
    Provides optimized queries for signal data access patterns
    common in trading applications.
    """
    
    async def create(self, signal: Signal) -> Signal:
        """
        Create a new trading signal.
        
        Args:
            signal: Signal entity to create
            
        Returns:
            Created signal with generated ID and timestamps
        """
        # Set audit fields
        now = datetime.now(timezone.utc)
        signal.created_at = now
        signal.updated_at = now
        
        # Implementation depends on database layer
        pass
    
    async def get_by_id(self, signal_id: str) -> Optional[Signal]:
        """Get signal by ID."""
        pass
    
    async def update(self, signal_id: str, updates: Dict[str, Any]) -> Optional[Signal]:
        """
        Update signal information.
        
        Args:
            signal_id: Signal's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated signal if found, None otherwise
        """
        # Set updated timestamp
        updates["updated_at"] = datetime.now(timezone.utc)
        pass
    
    async def delete(self, signal_id: str) -> bool:
        """Delete signal by ID."""
        pass
    
    async def list(self, options: Optional[QueryOptions] = None) -> List[Signal]:
        """List signals with optional filtering and pagination."""
        pass
    
    async def count(self, filters: Optional[List[QueryFilter]] = None) -> int:
        """Count signals matching the given filters."""
        pass
    
    async def exists(self, signal_id: str) -> bool:
        """Check if signal exists by ID."""
        signal = await self.get_by_id(signal_id)
        return signal is not None
    
    async def create_many(self, signals: List[Signal]) -> List[Signal]:
        """Create multiple signals in a single transaction."""
        created_signals = []
        for signal in signals:
            created_signal = await self.create(signal)
            created_signals.append(created_signal)
        return created_signals
    
    async def update_many(self, updates: List[Dict[str, Any]]) -> List[Signal]:
        """Update multiple signals in a single transaction."""
        updated_signals = []
        for update in updates:
            if "id" not in update:
                raise ValidationError("Signal ID required for bulk update")
            
            signal_id = update.pop("id")
            updated_signal = await self.update(signal_id, update)
            if updated_signal:
                updated_signals.append(updated_signal)
        return updated_signals
    
    async def delete_many(self, signal_ids: List[str]) -> int:
        """Delete multiple signals in a single transaction."""
        deleted_count = 0
        for signal_id in signal_ids:
            if await self.delete(signal_id):
                deleted_count += 1
        return deleted_count
    
    async def find_by_field(self, field: str, value: Any) -> List[Signal]:
        """Find signals by a specific field value."""
        pass
    
    async def find_one_by_field(self, field: str, value: Any) -> Optional[Signal]:
        """Find a single signal by a specific field value."""
        pass
    
    async def get_audit_history(self, signal_id: str) -> List[Dict[str, Any]]:
        """Get audit history for a signal."""
        pass
    
    async def get_created_by_user(self, user_id: str, options: Optional[QueryOptions] = None) -> List[Signal]:
        """Get signals created by a specific user."""
        return await self.find_by_field("user_id", user_id)
    
    async def get_modified_since(self, since_datetime: str, options: Optional[QueryOptions] = None) -> List[Signal]:
        """Get signals modified since a specific datetime."""
        filters = [QueryFilter(field="updated_at", operator="ge", value=since_datetime)]
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.list(options)
    
    # Signal-specific methods
    
    async def get_by_symbol(self, symbol: str, options: Optional[QueryOptions] = None) -> List[Signal]:
        """
        Get all signals for a specific trading symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            options: Query options for filtering and pagination
            
        Returns:
            List of signals for the symbol
        """
        return await self.find_by_field("symbol", symbol.upper())
    
    async def get_by_type(self, signal_type: SignalType, options: Optional[QueryOptions] = None) -> List[Signal]:
        """
        Get signals by type (BUY/SELL).
        
        Args:
            signal_type: Type of signal
            options: Query options for filtering and pagination
            
        Returns:
            List of signals of the specified type
        """
        return await self.find_by_field("signal_type", signal_type.value)
    
    async def get_recent_signals(
        self,
        limit: int = 50,
        hours_back: int = 24
    ) -> List[Signal]:
        """
        Get recent signals within the specified time window.
        
        Args:
            limit: Maximum number of signals to return
            hours_back: Number of hours back to look
            
        Returns:
            List of recent signals ordered by timestamp descending
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        options = QueryOptions(
            limit=limit,
            order_by="timestamp",
            order_direction="desc",
            filters=[
                QueryFilter(field="timestamp", operator="ge", value=cutoff_time.isoformat())
            ]
        )
        
        return await self.list(options)
    
    async def get_signals_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None,
        signal_type: Optional[SignalType] = None,
        options: Optional[QueryOptions] = None
    ) -> List[Signal]:
        """
        Get signals within a date range with optional filtering.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            symbol: Optional symbol filter
            signal_type: Optional signal type filter
            options: Additional query options
            
        Returns:
            List of signals matching the criteria
        """
        filters = [
            QueryFilter(field="timestamp", operator="ge", value=start_date.isoformat()),
            QueryFilter(field="timestamp", operator="le", value=end_date.isoformat())
        ]
        
        if symbol:
            filters.append(QueryFilter(field="symbol", operator="eq", value=symbol.upper()))
        
        if signal_type:
            filters.append(QueryFilter(field="signal_type", operator="eq", value=signal_type.value))
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(
                filters=filters,
                order_by="timestamp",
                order_direction="desc"
            )
        
        return await self.list(options)
    
    async def get_top_performing_signals(
        self,
        limit: int = 20,
        min_confidence: Optional[float] = None
    ) -> List[Signal]:
        """
        Get top performing signals based on confidence score.
        
        Args:
            limit: Maximum number of signals to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of signals ordered by confidence descending
        """
        filters = []
        if min_confidence is not None:
            filters.append(QueryFilter(field="confidence", operator="ge", value=min_confidence))
        
        options = QueryOptions(
            limit=limit,
            order_by="confidence",
            order_direction="desc",
            filters=filters
        )
        
        return await self.list(options)
    
    async def get_signals_by_user_and_symbol(
        self,
        user_id: str,
        symbol: str,
        options: Optional[QueryOptions] = None
    ) -> List[Signal]:
        """
        Get signals for a specific user and symbol combination.
        
        Args:
            user_id: User identifier
            symbol: Trading symbol
            options: Additional query options
            
        Returns:
            List of matching signals
        """
        filters = [
            QueryFilter(field="user_id", operator="eq", value=user_id),
            QueryFilter(field="symbol", operator="eq", value=symbol.upper())
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(
                filters=filters,
                order_by="timestamp",
                order_direction="desc"
            )
        
        return await self.list(options)
    
    async def get_signal_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get signal statistics for analytics.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Dictionary containing signal statistics
        """
        # This would be implemented with aggregate queries
        # depending on the database implementation
        filters = []
        if user_id:
            filters.append(QueryFilter(field="user_id", operator="eq", value=user_id))
        
        # Implementation would return something like:
        # {
        #     "total_signals": 1500,
        #     "buy_signals": 800,
        #     "sell_signals": 700,
        #     "avg_confidence": 0.75,
        #     "unique_symbols": 50,
        #     "signals_today": 25
        # }
        pass
    
    async def cleanup_old_signals(self, days_old: int = 90) -> int:
        """
        Clean up signals older than specified days.
        
        Args:
            days_old: Number of days after which to delete signals
            
        Returns:
            Number of signals deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        filters = [
            QueryFilter(field="timestamp", operator="lt", value=cutoff_date.isoformat())
        ]
        
        # Get signals to delete
        old_signals = await self.list(QueryOptions(filters=filters))
        signal_ids = [signal.id for signal in old_signals]
        
        return await self.delete_many(signal_ids)
    
    async def get_latest_signal_per_symbol(self, symbols: List[str]) -> Dict[str, Optional[Signal]]:
        """
        Get the latest signal for each symbol.
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            Dictionary mapping symbol to latest signal (or None)
        """
        result = {}
        
        for symbol in symbols:
            options = QueryOptions(
                limit=1,
                order_by="timestamp",
                order_direction="desc",
                filters=[QueryFilter(field="symbol", operator="eq", value=symbol.upper())]
            )
            
            signals = await self.list(options)
            result[symbol] = signals[0] if signals else None
        
        return result