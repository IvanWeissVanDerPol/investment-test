"""
Stripe webhook handler for processing payment events.
Keeps our database synchronized with Stripe events.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from investment_system.services.stripe_service import get_stripe_service
from investment_system.infrastructure.database import get_session, User, Subscription
from investment_system.core.contracts import UserTier
from investment_system.cache import invalidate_cache
from investment_system.security.audit import security_logger

logger = logging.getLogger(__name__)
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class StripeWebhookHandler:
    """Handles Stripe webhook events and updates our database accordingly."""
    
    def __init__(self):
        self.stripe_service = get_stripe_service()
    
    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, str]:
        """
        Process Stripe webhook event.
        
        Args:
            event: Stripe event object
            
        Returns:
            Processing result
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        
        logger.info(f"Processing Stripe webhook: {event_type}")
        
        try:
            if event_type == "customer.subscription.created":
                await self._handle_subscription_created(data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(data)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(data)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(data)
            elif event_type == "customer.subscription.trial_will_end":
                await self._handle_trial_ending(data)
            elif event_type == "customer.created":
                await self._handle_customer_created(data)
            elif event_type == "customer.updated":
                await self._handle_customer_updated(data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "reason": "unhandled_event_type"}
            
            # Log successful webhook processing
            await security_logger.log_event(
                event_type="webhook_processed",
                details={
                    "stripe_event_type": event_type,
                    "stripe_event_id": event.get("id"),
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Failed to process webhook {event_type}: {e}")
            
            # Log webhook processing failure
            await security_logger.log_event(
                event_type="webhook_failed",
                details={
                    "stripe_event_type": event_type,
                    "stripe_event_id": event.get("id"),
                    "error": str(e)
                },
                risk_score=6  # Medium risk
            )
            
            raise
    
    async def _handle_subscription_created(self, subscription: Dict[str, Any]):
        """Handle subscription creation."""
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        
        async with get_session() as session:
            # Find user by Stripe customer ID
            result = await session.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User not found for Stripe customer {customer_id}")
                return
            
            # Check if subscription already exists
            existing = await session.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Subscription {subscription_id} already exists")
                return
            
            # Extract tier from metadata
            metadata = subscription.get("metadata", {})
            tier_str = metadata.get("tier", "starter")
            tier = UserTier(tier_str)
            
            # Create subscription record
            new_subscription = Subscription(
                id=subscription_id,
                user_id=user.id,
                stripe_subscription_id=subscription_id,
                tier=tier,
                status=status,
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                monthly_amount=subscription.get("items", {}).get("data", [{}])[0].get("price", {}).get("unit_amount", 0),
                created_at=datetime.utcnow()
            )
            
            session.add(new_subscription)
            
            # Update user tier
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(tier=tier, updated_at=datetime.utcnow())
            )
            
            await session.commit()
            
            # Invalidate caches
            invalidate_cache(f"customer_subscription:{user.id}")
            invalidate_cache(f"user:*{user.id}*")
            
            logger.info(f"Created subscription {subscription_id} for user {user.id}")
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription updates."""
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        
        async with get_session() as session:
            # Update subscription status
            result = await session.execute(
                update(Subscription)
                .where(Subscription.stripe_subscription_id == subscription_id)
                .values(
                    status=status,
                    current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                    current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                    updated_at=datetime.utcnow()
                )
            )
            
            if result.rowcount == 0:
                logger.warning(f"Subscription {subscription_id} not found for update")
                return
            
            await session.commit()
            
            # Get user ID for cache invalidation
            result = await session.execute(
                select(Subscription.user_id).where(Subscription.stripe_subscription_id == subscription_id)
            )
            user_id = result.scalar_one_or_none()
            
            if user_id:
                invalidate_cache(f"customer_subscription:{user_id}")
            
            logger.info(f"Updated subscription {subscription_id} status to {status}")
    
    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation."""
        subscription_id = subscription.get("id")
        
        async with get_session() as session:
            # Get subscription with user
            result = await session.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
            )
            sub = result.scalar_one_or_none()
            
            if not sub:
                logger.warning(f"Subscription {subscription_id} not found for deletion")
                return
            
            # Update subscription status
            await session.execute(
                update(Subscription)
                .where(Subscription.id == sub.id)
                .values(
                    status="canceled",
                    canceled_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            # Downgrade user to free tier
            await session.execute(
                update(User)
                .where(User.id == sub.user_id)
                .values(tier=UserTier.FREE, updated_at=datetime.utcnow())
            )
            
            await session.commit()
            
            # Invalidate caches
            invalidate_cache(f"customer_subscription:{sub.user_id}")
            invalidate_cache(f"user:*{sub.user_id}*")
            
            logger.info(f"Canceled subscription {subscription_id} for user {sub.user_id}")
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]):
        """Handle successful payment."""
        subscription_id = invoice.get("subscription")
        amount_paid = invoice.get("amount_paid", 0)
        
        if not subscription_id:
            return
        
        async with get_session() as session:
            # Record payment success (you could create a Payment table)
            result = await session.execute(
                select(Subscription.user_id).where(Subscription.stripe_subscription_id == subscription_id)
            )
            user_id = result.scalar_one_or_none()
            
            if user_id:
                logger.info(f"Payment succeeded for subscription {subscription_id}: ${amount_paid/100:.2f}")
                
                # You could send email notification here
                # await send_payment_confirmation_email(user_id, amount_paid)
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment."""
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")
        
        async with get_session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.warning(f"Payment failed for user {user.id}, subscription {subscription_id}")
                
                # Log security event for failed payments
                await security_logger.log_event(
                    user_id=user.id,
                    event_type="payment_failed",
                    details={
                        "subscription_id": subscription_id,
                        "customer_id": customer_id,
                        "amount": invoice.get("amount_due", 0)
                    },
                    risk_score=4
                )
                
                # You could send email notification or start dunning process
                # await handle_failed_payment_dunning(user.id)
    
    async def _handle_trial_ending(self, subscription: Dict[str, Any]):
        """Handle trial period ending."""
        customer_id = subscription.get("customer")
        
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(f"Trial ending for user {user.id}")
                # Send trial ending notification email
                # await send_trial_ending_email(user.id)
    
    async def _handle_customer_created(self, customer: Dict[str, Any]):
        """Handle customer creation."""
        customer_id = customer.get("id")
        email = customer.get("email")
        
        logger.info(f"Stripe customer created: {customer_id} ({email})")
    
    async def _handle_customer_updated(self, customer: Dict[str, Any]):
        """Handle customer updates."""
        customer_id = customer.get("id")
        email = customer.get("email")
        
        # Update user email if changed
        async with get_session() as session:
            await session.execute(
                update(User)
                .where(User.stripe_customer_id == customer_id)
                .values(email=email, updated_at=datetime.utcnow())
            )
            await session.commit()


# Global handler instance
webhook_handler = StripeWebhookHandler()


@webhook_router.post("/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Stripe webhook endpoint.
    
    This endpoint receives and processes Stripe webhook events.
    """
    try:
        # Get request body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook signature and construct event
        stripe_service = get_stripe_service()
        event = stripe_service.construct_webhook_event(payload, signature)
        
        # Process event in background
        background_tasks.add_task(webhook_handler.handle_webhook_event, event)
        
        return {"status": "received"}
        
    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@webhook_router.get("/stripe/test")
async def test_webhook():
    """Test endpoint to verify webhook handler is working."""
    return {
        "status": "webhook_handler_ready",
        "stripe_enabled": get_stripe_service().enabled,
        "timestamp": datetime.utcnow().isoformat()
    }