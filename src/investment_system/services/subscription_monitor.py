"""
Subscription monitoring service for proactive management.
Handles subscription lifecycle, renewals, and notifications.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from investment_system.infrastructure.database import get_session, User, Subscription
from investment_system.services.stripe_service import get_stripe_service
from investment_system.services.billing_service import get_billing_service
from investment_system.core.contracts import UserTier
from investment_system.cache import cached, invalidate_cache
from investment_system.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


class SubscriptionMonitor:
    """
    Monitors subscription lifecycle and handles proactive management.
    Checks for expiring subscriptions, failed payments, and sync issues.
    """
    
    def __init__(self):
        self.stripe_service = get_stripe_service()
        self.billing_service = get_billing_service()
    
    async def check_subscription_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive subscription health check.
        
        Returns:
            Health check report
        """
        async with get_session() as session:
            try:
                # Get all active subscriptions
                result = await session.execute(
                    select(Subscription)
                    .where(Subscription.status.in_(["active", "trialing", "past_due"]))
                )
                subscriptions = result.scalars().all()
                
                health_report = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_active_subscriptions": len(subscriptions),
                    "issues": [],
                    "actions_taken": [],
                    "summary": {
                        "healthy": 0,
                        "expiring_soon": 0,
                        "past_due": 0,
                        "sync_issues": 0
                    }
                }
                
                for subscription in subscriptions:
                    issue_found = await self._check_individual_subscription(
                        session, subscription, health_report
                    )
                    
                    if not issue_found:
                        health_report["summary"]["healthy"] += 1
                
                logger.info(f"Subscription health check completed: {health_report['summary']}")
                return health_report
                
            except Exception as e:
                logger.error(f"Subscription health check failed: {e}")
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "status": "failed"
                }
    
    async def _check_individual_subscription(
        self,
        session: AsyncSession,
        subscription: Subscription,
        report: Dict[str, Any]
    ) -> bool:
        """
        Check individual subscription for issues.
        
        Args:
            session: Database session
            subscription: Subscription to check
            report: Health report to update
            
        Returns:
            True if issue found, False otherwise
        """
        issue_found = False
        now = datetime.utcnow()
        
        # Check if subscription is expiring soon (within 7 days)
        if subscription.current_period_end:
            days_until_expiry = (subscription.current_period_end - now).days
            
            if 0 <= days_until_expiry <= 7:
                report["issues"].append({
                    "type": "expiring_soon",
                    "subscription_id": subscription.id,
                    "user_id": subscription.user_id,
                    "expires_in_days": days_until_expiry,
                    "expires_at": subscription.current_period_end.isoformat()
                })
                report["summary"]["expiring_soon"] += 1
                issue_found = True
        
        # Check if subscription is past due
        if subscription.status == "past_due":
            report["issues"].append({
                "type": "past_due",
                "subscription_id": subscription.id,
                "user_id": subscription.user_id,
                "status": subscription.status
            })
            report["summary"]["past_due"] += 1
            issue_found = True
        
        # Check for Stripe sync issues if enabled
        if self.stripe_service.enabled and subscription.stripe_subscription_id:
            try:
                stripe_sub = await self.stripe_service.get_subscription(
                    subscription.stripe_subscription_id
                )
                
                # Compare status
                if stripe_sub["status"] != subscription.status:
                    report["issues"].append({
                        "type": "status_sync_issue",
                        "subscription_id": subscription.id,
                        "user_id": subscription.user_id,
                        "local_status": subscription.status,
                        "stripe_status": stripe_sub["status"]
                    })
                    report["summary"]["sync_issues"] += 1
                    issue_found = True
                    
                    # Auto-fix: update local status to match Stripe
                    await session.execute(
                        update(Subscription)
                        .where(Subscription.id == subscription.id)
                        .values(
                            status=stripe_sub["status"],
                            updated_at=now
                        )
                    )
                    report["actions_taken"].append(
                        f"Updated subscription {subscription.id} status to {stripe_sub['status']}"
                    )
                
            except Exception as e:
                logger.warning(f"Could not sync subscription {subscription.id} with Stripe: {e}")
                report["issues"].append({
                    "type": "stripe_sync_error",
                    "subscription_id": subscription.id,
                    "user_id": subscription.user_id,
                    "error": str(e)
                })
                issue_found = True
        
        return issue_found
    
    async def get_expiring_subscriptions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get subscriptions expiring within specified days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring subscriptions
        """
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        async with get_session() as session:
            result = await session.execute(
                select(Subscription)
                .where(Subscription.status == "active")
                .where(Subscription.current_period_end <= end_date)
                .where(Subscription.current_period_end > datetime.utcnow())
            )
            
            expiring = []
            for subscription in result.scalars():
                # Get user info
                user_result = await session.execute(
                    select(User).where(User.id == subscription.user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if user:
                    days_remaining = (subscription.current_period_end - datetime.utcnow()).days
                    
                    expiring.append({
                        "subscription_id": subscription.id,
                        "user_id": user.id,
                        "user_email": user.email,
                        "tier": subscription.tier.value,
                        "expires_at": subscription.current_period_end.isoformat(),
                        "days_remaining": days_remaining,
                        "monthly_amount": subscription.monthly_amount
                    })
            
            return expiring
    
    async def handle_subscription_expiry(self, subscription_id: str) -> Dict[str, Any]:
        """
        Handle expired subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Handling result
        """
        async with get_session() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.id == subscription_id)
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {"error": "Subscription not found"}
            
            if subscription.current_period_end > datetime.utcnow():
                return {"error": "Subscription not yet expired"}
            
            # Update subscription status
            await session.execute(
                update(Subscription)
                .where(Subscription.id == subscription_id)
                .values(
                    status="expired",
                    updated_at=datetime.utcnow()
                )
            )
            
            # Downgrade user to free tier
            await session.execute(
                update(User)
                .where(User.id == subscription.user_id)
                .values(
                    tier=UserTier.FREE,
                    updated_at=datetime.utcnow()
                )
            )
            
            await session.commit()
            
            # Clear caches
            invalidate_cache(f"customer_subscription:{subscription.user_id}")
            invalidate_cache(f"user:*{subscription.user_id}*")
            
            logger.info(f"Handled expired subscription {subscription_id}")
            
            return {
                "subscription_id": subscription_id,
                "user_id": subscription.user_id,
                "action": "downgraded_to_free",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @cached(ttl=3600, key_prefix="subscription_stats")
    async def get_subscription_statistics(self) -> Dict[str, Any]:
        """
        Get subscription statistics for monitoring.
        
        Returns:
            Subscription statistics
        """
        async with get_session() as session:
            # Count by status
            status_result = await session.execute(
                select(Subscription.status, Subscription.tier)
            )
            
            stats = {
                "by_status": {},
                "by_tier": {},
                "total": 0,
                "revenue": {
                    "monthly_recurring": 0,
                    "by_tier": {}
                }
            }
            
            for row in status_result:
                status = row.status
                tier = row.tier
                
                # Count by status
                if status not in stats["by_status"]:
                    stats["by_status"][status] = 0
                stats["by_status"][status] += 1
                
                # Count by tier
                if tier not in stats["by_tier"]:
                    stats["by_tier"][tier.value] = 0
                stats["by_tier"][tier.value] += 1
                
                stats["total"] += 1
            
            # Calculate revenue for active subscriptions
            revenue_result = await session.execute(
                select(Subscription.tier, Subscription.monthly_amount)
                .where(Subscription.status == "active")
            )
            
            for row in revenue_result:
                tier = row.tier.value
                amount = row.monthly_amount or 0
                
                stats["revenue"]["monthly_recurring"] += amount
                
                if tier not in stats["revenue"]["by_tier"]:
                    stats["revenue"]["by_tier"][tier] = 0
                stats["revenue"]["by_tier"][tier] += amount
            
            # Convert cents to dollars
            stats["revenue"]["monthly_recurring_usd"] = stats["revenue"]["monthly_recurring"] / 100
            stats["revenue"]["annual_recurring_usd"] = stats["revenue"]["monthly_recurring_usd"] * 12
            
            return stats
    
    async def send_expiry_notifications(self, days_ahead: int = 3) -> Dict[str, Any]:
        """
        Send notifications for expiring subscriptions.
        
        Args:
            days_ahead: Send notifications for subscriptions expiring within this many days
            
        Returns:
            Notification results
        """
        expiring = await self.get_expiring_subscriptions(days_ahead)
        
        notifications_sent = 0
        errors = []
        
        for subscription in expiring:
            try:
                # In a real implementation, you would send email notifications here
                # await send_expiry_notification_email(
                #     subscription["user_email"],
                #     subscription["expires_at"],
                #     subscription["tier"]
                # )
                
                logger.info(
                    f"Would send expiry notification to {subscription['user_email']} "
                    f"for subscription expiring in {subscription['days_remaining']} days"
                )
                notifications_sent += 1
                
            except Exception as e:
                error_msg = f"Failed to notify {subscription['user_email']}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            "subscriptions_checked": len(expiring),
            "notifications_sent": notifications_sent,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global monitor instance
_subscription_monitor: Optional[SubscriptionMonitor] = None


def get_subscription_monitor() -> SubscriptionMonitor:
    """Get global subscription monitor instance."""
    global _subscription_monitor
    if _subscription_monitor is None:
        _subscription_monitor = SubscriptionMonitor()
    return _subscription_monitor