"""
Usage tracking service for billing and analytics.
Tracks API usage, signal generations, and other billable events.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from investment_system.infrastructure.database import get_session, User, APIUsage
from investment_system.core.contracts import UserTier
from investment_system.cache import cached
from investment_system.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks user usage for billing purposes.
    Records API calls, signal generations, and calculates overages.
    """
    
    def __init__(self):
        pass
    
    @retry_with_backoff(retries=2, backoff_in_seconds=0.5)
    async def record_usage(
        self,
        user_id: str,
        endpoint: str,
        method: str = "POST",
        cost_units: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record API usage for a user.
        
        Args:
            user_id: User ID
            endpoint: API endpoint accessed
            method: HTTP method
            cost_units: Number of units consumed (e.g., signals generated)
            metadata: Optional metadata about the request
            
        Returns:
            Usage record details
        """
        async with get_session() as session:
            try:
                # Create usage record
                usage_record = APIUsage(
                    user_id=user_id,
                    endpoint=endpoint,
                    method=method,
                    cost_units=cost_units,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                
                session.add(usage_record)
                await session.commit()
                
                logger.debug(f"Recorded usage for user {user_id}: {endpoint} ({cost_units} units)")
                
                return {
                    "usage_id": usage_record.id,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "cost_units": cost_units,
                    "timestamp": usage_record.created_at
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to record usage for user {user_id}: {e}")
                # Don't fail the main request for usage tracking issues
                return {"error": str(e)}
    
    @cached(ttl=300, key_prefix="user_usage_current")
    async def get_current_usage(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get user's current usage statistics.
        
        Args:
            user_id: User ID
            period_start: Start of period (defaults to start of current month)
            period_end: End of period (defaults to now)
            
        Returns:
            Usage statistics
        """
        if not period_start:
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if not period_end:
            period_end = datetime.utcnow()
        
        async with get_session() as session:
            try:
                # Get total usage in period
                total_result = await session.execute(
                    select(func.sum(APIUsage.cost_units))
                    .where(APIUsage.user_id == user_id)
                    .where(APIUsage.created_at >= period_start)
                    .where(APIUsage.created_at <= period_end)
                )
                total_usage = total_result.scalar() or 0
                
                # Get usage by endpoint
                endpoint_result = await session.execute(
                    select(
                        APIUsage.endpoint,
                        func.sum(APIUsage.cost_units).label('total_units'),
                        func.count(APIUsage.id).label('total_calls')
                    )
                    .where(APIUsage.user_id == user_id)
                    .where(APIUsage.created_at >= period_start)
                    .where(APIUsage.created_at <= period_end)
                    .group_by(APIUsage.endpoint)
                )
                endpoint_usage = [
                    {
                        "endpoint": row.endpoint,
                        "units": int(row.total_units),
                        "calls": int(row.total_calls)
                    }
                    for row in endpoint_result
                ]
                
                # Get recent usage (last 10 calls)
                recent_result = await session.execute(
                    select(APIUsage)
                    .where(APIUsage.user_id == user_id)
                    .order_by(desc(APIUsage.created_at))
                    .limit(10)
                )
                recent_usage = [
                    {
                        "endpoint": usage.endpoint,
                        "method": usage.method,
                        "units": usage.cost_units,
                        "timestamp": usage.created_at.isoformat()
                    }
                    for usage in recent_result.scalars()
                ]
                
                return {
                    "user_id": user_id,
                    "period": {
                        "start": period_start.isoformat(),
                        "end": period_end.isoformat()
                    },
                    "usage": {
                        "total_units": int(total_usage),
                        "by_endpoint": endpoint_usage,
                        "recent": recent_usage
                    }
                }
                
            except Exception as e:
                logger.error(f"Failed to get usage for user {user_id}: {e}")
                return {
                    "user_id": user_id,
                    "usage": {"total_units": 0, "by_endpoint": [], "recent": []},
                    "error": str(e)
                }
    
    async def calculate_overage_and_billing(
        self,
        user_id: str,
        current_usage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate overage charges and billing information.
        
        Args:
            user_id: User ID
            current_usage: Current usage (if not provided, will be calculated)
            
        Returns:
            Billing calculation
        """
        async with get_session() as session:
            # Get user
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get current usage if not provided
            if current_usage is None:
                usage_data = await self.get_current_usage(user_id)
                current_usage = usage_data["usage"]["total_units"]
            
            # Define tier limits and pricing
            tier_config = {
                UserTier.FREE: {
                    "included_units": 100,
                    "overage_rate_cents": None,  # No overage allowed
                    "monthly_cost_cents": 0
                },
                UserTier.STARTER: {
                    "included_units": 1000,
                    "overage_rate_cents": 3,  # 3 cents per unit
                    "monthly_cost_cents": 2900
                },
                UserTier.PRO: {
                    "included_units": 10000,
                    "overage_rate_cents": 2,  # 2 cents per unit
                    "monthly_cost_cents": 9900
                },
                UserTier.ENTERPRISE: {
                    "included_units": 100000,
                    "overage_rate_cents": 1,  # 1 cent per unit
                    "monthly_cost_cents": 49900
                }
            }
            
            config = tier_config.get(user.tier, tier_config[UserTier.FREE])
            included = config["included_units"]
            overage_rate = config["overage_rate_cents"]
            monthly_cost = config["monthly_cost_cents"]
            
            # Calculate overage
            overage_units = max(0, current_usage - included)
            overage_cost_cents = 0
            
            if overage_units > 0:
                if user.tier == UserTier.FREE:
                    # Free tier users hit limit, no overage allowed
                    overage_blocked = True
                    overage_cost_cents = 0
                else:
                    overage_blocked = False
                    overage_cost_cents = overage_units * overage_rate
            else:
                overage_blocked = False
            
            remaining_units = max(0, included - current_usage)
            usage_percentage = min(100, (current_usage / included) * 100)
            
            return {
                "user_id": user_id,
                "tier": user.tier.value,
                "billing": {
                    "monthly_cost_cents": monthly_cost,
                    "monthly_cost_usd": monthly_cost / 100,
                    "included_units": included,
                    "current_usage": current_usage,
                    "remaining_units": remaining_units,
                    "usage_percentage": round(usage_percentage, 1),
                    "overage_units": overage_units,
                    "overage_cost_cents": overage_cost_cents,
                    "overage_cost_usd": overage_cost_cents / 100,
                    "total_cost_cents": monthly_cost + overage_cost_cents,
                    "total_cost_usd": (monthly_cost + overage_cost_cents) / 100,
                    "overage_blocked": overage_blocked
                },
                "limits": {
                    "at_limit": current_usage >= included,
                    "approaching_limit": usage_percentage > 80,
                    "over_limit": current_usage > included
                }
            }
    
    async def check_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has hit usage limits.
        
        Args:
            user_id: User ID
            
        Returns:
            Limit check results
        """
        billing_info = await self.calculate_overage_and_billing(user_id)
        limits = billing_info["limits"]
        
        return {
            "allowed": not (limits["at_limit"] and billing_info["billing"]["overage_blocked"]),
            "reason": "usage_limit_exceeded" if limits["at_limit"] else None,
            "limits": limits,
            "current_usage": billing_info["billing"]["current_usage"],
            "included_units": billing_info["billing"]["included_units"]
        }
    
    async def get_usage_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage analytics for a user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Usage analytics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        async with get_session() as session:
            # Daily usage trend
            daily_result = await session.execute(
                select(
                    func.date(APIUsage.created_at).label('date'),
                    func.sum(APIUsage.cost_units).label('units')
                )
                .where(APIUsage.user_id == user_id)
                .where(APIUsage.created_at >= start_date)
                .group_by(func.date(APIUsage.created_at))
                .order_by(func.date(APIUsage.created_at))
            )
            
            daily_usage = [
                {
                    "date": str(row.date),
                    "units": int(row.units)
                }
                for row in daily_result
            ]
            
            # Peak usage hours
            hourly_result = await session.execute(
                select(
                    func.extract('hour', APIUsage.created_at).label('hour'),
                    func.count(APIUsage.id).label('calls')
                )
                .where(APIUsage.user_id == user_id)
                .where(APIUsage.created_at >= start_date)
                .group_by(func.extract('hour', APIUsage.created_at))
                .order_by(func.count(APIUsage.id).desc())
                .limit(5)
            )
            
            peak_hours = [
                {
                    "hour": int(row.hour),
                    "calls": int(row.calls)
                }
                for row in hourly_result
            ]
            
            return {
                "user_id": user_id,
                "period_days": days,
                "daily_usage": daily_usage,
                "peak_hours": peak_hours,
                "total_days_analyzed": len(daily_usage)
            }


# Global tracker instance
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get global usage tracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker