"""
Billing service that manages customer lifecycle and integrates with Stripe.
Handles the bridge between our database and Stripe.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from investment_system.infrastructure.database import get_session, User, Subscription
from investment_system.services.stripe_service import get_stripe_service
from investment_system.core.contracts import UserTier
from investment_system.cache import cached, invalidate_cache
from investment_system.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


class BillingService:
    """
    Manages customer billing lifecycle and Stripe integration.
    Synchronizes data between our database and Stripe.
    """
    
    def __init__(self):
        self.stripe_service = get_stripe_service()
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    async def create_customer_and_subscription(
        self,
        user_id: str,
        tier: UserTier,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Create a new customer and subscription in both Stripe and our database.
        
        Args:
            user_id: Internal user ID
            tier: Subscription tier
            payment_method_id: Stripe payment method ID
            
        Returns:
            Complete customer and subscription data
        """
        async with get_session() as session:
            # Get user
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if not self.stripe_service.enabled:
                # Mock mode for development
                return await self._create_mock_subscription(session, user, tier)
            
            try:
                # Create Stripe customer
                customer_data = await self.stripe_service.create_customer(
                    user, payment_method_id
                )
                
                # Create Stripe subscription
                subscription_data = await self.stripe_service.create_subscription(
                    customer_data["customer_id"],
                    tier,
                    payment_method_id
                )
                
                # Update user with Stripe customer ID
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        stripe_customer_id=customer_data["customer_id"],
                        tier=tier,
                        updated_at=datetime.utcnow()
                    )
                )
                
                # Create subscription record
                subscription = Subscription(
                    id=subscription_data["subscription_id"],
                    user_id=user_id,
                    stripe_subscription_id=subscription_data["subscription_id"],
                    tier=tier,
                    status="active",
                    current_period_start=subscription_data["current_period_start"],
                    current_period_end=subscription_data["current_period_end"],
                    monthly_amount=subscription_data["monthly_price"],
                    created_at=datetime.utcnow()
                )
                
                session.add(subscription)
                await session.commit()
                
                # Invalidate user cache
                invalidate_cache(f"user:*{user_id}*")
                
                logger.info(f"Created subscription {subscription.id} for user {user_id}")
                
                return {
                    "customer": customer_data,
                    "subscription": subscription_data,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "tier": tier.value,
                        "stripe_customer_id": customer_data["customer_id"]
                    }
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create customer/subscription for user {user_id}: {e}")
                raise
    
    async def _create_mock_subscription(
        self,
        session: AsyncSession,
        user: User,
        tier: UserTier
    ) -> Dict[str, Any]:
        """Create mock subscription for development without Stripe."""
        mock_customer_id = f"cus_mock_{user.id[:8]}"
        mock_subscription_id = f"sub_mock_{user.id[:8]}"
        
        # Mock pricing
        pricing = {
            UserTier.STARTER: 2900,
            UserTier.PRO: 9900,
            UserTier.ENTERPRISE: 49900
        }
        
        # Update user
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                stripe_customer_id=mock_customer_id,
                tier=tier,
                updated_at=datetime.utcnow()
            )
        )
        
        # Create subscription record
        subscription = Subscription(
            id=mock_subscription_id,
            user_id=user.id,
            stripe_subscription_id=mock_subscription_id,
            tier=tier,
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            monthly_amount=pricing.get(tier, 0),
            created_at=datetime.utcnow()
        )
        
        session.add(subscription)
        await session.commit()
        
        logger.info(f"Created mock subscription for user {user.id}")
        
        return {
            "customer": {
                "customer_id": mock_customer_id,
                "email": user.email,
                "created": datetime.utcnow()
            },
            "subscription": {
                "subscription_id": mock_subscription_id,
                "customer_id": mock_customer_id,
                "status": "active",
                "tier": tier,
                "monthly_price": pricing.get(tier, 0)
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "tier": tier.value,
                "stripe_customer_id": mock_customer_id
            }
        }
    
    @cached(ttl=300, key_prefix="customer_subscription")
    async def get_customer_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer subscription details.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Subscription data or None if not found
        """
        async with get_session() as session:
            # Get user with subscription
            result = await session.execute(
                select(User)
                .options(selectinload(User.subscriptions))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.subscriptions:
                return None
            
            # Get active subscription
            active_subscription = None
            for sub in user.subscriptions:
                if sub.status == "active":
                    active_subscription = sub
                    break
            
            if not active_subscription:
                return None
            
            # Get Stripe subscription details if available
            stripe_details = {}
            if self.stripe_service.enabled and active_subscription.stripe_subscription_id:
                try:
                    stripe_details = await self.stripe_service.get_subscription(
                        active_subscription.stripe_subscription_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to get Stripe subscription: {e}")
            
            return {
                "subscription_id": active_subscription.id,
                "user_id": user_id,
                "tier": active_subscription.tier,
                "status": active_subscription.status,
                "current_period_start": active_subscription.current_period_start,
                "current_period_end": active_subscription.current_period_end,
                "monthly_amount": active_subscription.monthly_amount,
                "stripe_subscription_id": active_subscription.stripe_subscription_id,
                "stripe_customer_id": user.stripe_customer_id,
                "stripe_details": stripe_details
            }
    
    async def cancel_subscription(
        self,
        user_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel user subscription.
        
        Args:
            user_id: Internal user ID
            at_period_end: Whether to cancel at period end
            
        Returns:
            Cancellation result
        """
        async with get_session() as session:
            # Get active subscription
            result = await session.execute(
                select(Subscription)
                .where(Subscription.user_id == user_id)
                .where(Subscription.status == "active")
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                raise ValueError("No active subscription found")
            
            try:
                # Cancel in Stripe if enabled
                stripe_result = {}
                if self.stripe_service.enabled and subscription.stripe_subscription_id:
                    stripe_result = await self.stripe_service.cancel_subscription(
                        subscription.stripe_subscription_id,
                        at_period_end
                    )
                
                # Update database
                new_status = "canceled" if not at_period_end else "canceling"
                await session.execute(
                    update(Subscription)
                    .where(Subscription.id == subscription.id)
                    .values(
                        status=new_status,
                        canceled_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                
                # Downgrade user to free tier if immediate cancellation
                if not at_period_end:
                    await session.execute(
                        update(User)
                        .where(User.id == user_id)
                        .values(
                            tier=UserTier.FREE,
                            updated_at=datetime.utcnow()
                        )
                    )
                
                await session.commit()
                
                # Invalidate cache
                invalidate_cache(f"customer_subscription:{user_id}")
                invalidate_cache(f"user:*{user_id}*")
                
                logger.info(f"Canceled subscription {subscription.id} for user {user_id}")
                
                return {
                    "subscription_id": subscription.id,
                    "status": new_status,
                    "canceled_at": datetime.utcnow(),
                    "at_period_end": at_period_end,
                    "stripe_result": stripe_result
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to cancel subscription for user {user_id}: {e}")
                raise
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_tier: UserTier,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade user subscription to a new tier.
        
        Args:
            user_id: Internal user ID
            new_tier: New subscription tier
            payment_method_id: Optional new payment method
            
        Returns:
            Upgrade result
        """
        current_subscription = await self.get_customer_subscription(user_id)
        
        if not current_subscription:
            # Create new subscription
            return await self.create_customer_and_subscription(
                user_id, new_tier, payment_method_id
            )
        
        if current_subscription["tier"] == new_tier:
            raise ValueError(f"User already on {new_tier.value} tier")
        
        # For now, cancel current and create new
        # In production, you'd want to use Stripe's subscription modification
        await self.cancel_subscription(user_id, at_period_end=False)
        
        return await self.create_customer_and_subscription(
            user_id, new_tier, payment_method_id
        )
    
    @cached(ttl=3600, key_prefix="billing_usage")
    async def get_billing_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get user billing usage statistics.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Usage statistics
        """
        # Get subscription
        subscription = await self.get_customer_subscription(user_id)
        if not subscription:
            return {"error": "No active subscription"}
        
        # Calculate current billing period
        period_start = subscription["current_period_start"]
        period_end = subscription["current_period_end"]
        
        # Get usage from database (you'd implement this based on your usage tracking)
        async with get_session() as session:
            # Mock usage calculation for now
            # In production, query APIUsage table
            current_usage = 150  # Mock value
        
        # Calculate overage
        overage_calc = await self.stripe_service.calculate_overage_charges(
            user=None,  # We'll need to adjust this
            current_usage=current_usage,
            billing_period_start=period_start
        )
        
        return {
            "subscription": subscription,
            "billing_period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "days_remaining": (period_end - datetime.utcnow()).days
            },
            "usage": {
                "current": current_usage,
                **overage_calc
            }
        }


# Global service instance
_billing_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """Get global billing service instance."""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service