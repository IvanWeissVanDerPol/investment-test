"""
Billing API handlers for subscription management and payments.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Depends, status
from pydantic import BaseModel, Field
import logging

from investment_system.services.billing_service import get_billing_service
from investment_system.services.stripe_service import get_stripe_service
from investment_system.core.contracts import User, UserTier
from investment_system.cache import cached
from investment_system.security.audit import security_logger

logger = logging.getLogger(__name__)


# Request/Response models
class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription."""
    tier: UserTier = Field(..., description="Subscription tier")
    payment_method_id: str = Field(..., description="Stripe payment method ID")


class UpgradeSubscriptionRequest(BaseModel):
    """Request to upgrade subscription."""
    new_tier: UserTier = Field(..., description="New subscription tier")
    payment_method_id: Optional[str] = Field(None, description="Optional new payment method")


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription."""
    at_period_end: bool = Field(True, description="Cancel at period end or immediately")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class PaymentMethodRequest(BaseModel):
    """Request to add payment method."""
    payment_method_id: str = Field(..., description="Stripe payment method ID")
    set_as_default: bool = Field(True, description="Set as default payment method")


class BillingHandler:
    """Handles billing and subscription operations."""
    
    def __init__(self):
        self.billing_service = get_billing_service()
        self.stripe_service = get_stripe_service()
    
    async def create_subscription(
        self,
        request: CreateSubscriptionRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Create a new subscription for user.
        
        Args:
            request: Subscription creation request
            user: Authenticated user
            
        Returns:
            Subscription details
        """
        try:
            # Log subscription creation attempt
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_create_attempt",
                details={
                    "tier": request.tier.value,
                    "has_payment_method": bool(request.payment_method_id)
                }
            )
            
            # Check if user already has active subscription
            existing = await self.billing_service.get_customer_subscription(user.id)
            if existing and existing.get("status") == "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has an active subscription"
                )
            
            # Create subscription
            result = await self.billing_service.create_customer_and_subscription(
                user_id=user.id,
                tier=request.tier,
                payment_method_id=request.payment_method_id
            )
            
            # Log successful subscription creation
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_created",
                details={
                    "subscription_id": result["subscription"]["subscription_id"],
                    "tier": request.tier.value,
                    "customer_id": result["customer"]["customer_id"]
                }
            )
            
            logger.info(f"Created subscription for user {user.id} on tier {request.tier}")
            
            return {
                "success": True,
                "message": f"Successfully subscribed to {request.tier.value} tier",
                "subscription": result["subscription"],
                "customer": result["customer"]
            }
            
        except ValueError as e:
            logger.error(f"Subscription creation failed for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error creating subscription for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subscription"
            )
    
    async def get_subscription_status(self, user: User) -> Dict[str, Any]:
        """
        Get user's subscription status.
        
        Args:
            user: Authenticated user
            
        Returns:
            Subscription status and details
        """
        try:
            subscription = await self.billing_service.get_customer_subscription(user.id)
            
            if not subscription:
                return {
                    "has_subscription": False,
                    "tier": UserTier.FREE.value,
                    "status": "free",
                    "message": "No active subscription"
                }
            
            # Get usage information
            usage = await self.billing_service.get_billing_usage(user.id)
            
            return {
                "has_subscription": True,
                "subscription": subscription,
                "usage": usage,
                "tier": subscription["tier"].value,
                "status": subscription["status"],
                "expires_at": subscription["current_period_end"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription status for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subscription status"
            )
    
    async def upgrade_subscription(
        self,
        request: UpgradeSubscriptionRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Upgrade user's subscription tier.
        
        Args:
            request: Upgrade request
            user: Authenticated user
            
        Returns:
            Upgrade result
        """
        try:
            # Log upgrade attempt
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_upgrade_attempt",
                details={
                    "current_tier": user.tier.value,
                    "target_tier": request.new_tier.value
                }
            )
            
            # Validate upgrade
            current_subscription = await self.billing_service.get_customer_subscription(user.id)
            if not current_subscription:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active subscription to upgrade"
                )
            
            current_tier = current_subscription["tier"]
            if current_tier == request.new_tier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Already on {request.new_tier.value} tier"
                )
            
            # Perform upgrade
            result = await self.billing_service.upgrade_subscription(
                user_id=user.id,
                new_tier=request.new_tier,
                payment_method_id=request.payment_method_id
            )
            
            # Log successful upgrade
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_upgraded",
                details={
                    "from_tier": current_tier.value,
                    "to_tier": request.new_tier.value,
                    "subscription_id": result["subscription"]["subscription_id"]
                }
            )
            
            logger.info(f"Upgraded user {user.id} from {current_tier} to {request.new_tier}")
            
            return {
                "success": True,
                "message": f"Successfully upgraded to {request.new_tier.value} tier",
                "previous_tier": current_tier.value,
                "new_tier": request.new_tier.value,
                "subscription": result["subscription"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Subscription upgrade failed for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upgrade subscription"
            )
    
    async def cancel_subscription(
        self,
        request: CancelSubscriptionRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Cancel user's subscription.
        
        Args:
            request: Cancellation request
            user: Authenticated user
            
        Returns:
            Cancellation result
        """
        try:
            # Log cancellation attempt
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_cancel_attempt",
                details={
                    "at_period_end": request.at_period_end,
                    "reason": request.reason
                }
            )
            
            # Cancel subscription
            result = await self.billing_service.cancel_subscription(
                user_id=user.id,
                at_period_end=request.at_period_end
            )
            
            # Log successful cancellation
            await security_logger.log_event(
                user_id=user.id,
                event_type="subscription_canceled",
                details={
                    "subscription_id": result["subscription_id"],
                    "at_period_end": request.at_period_end,
                    "canceled_at": result["canceled_at"].isoformat()
                }
            )
            
            cancellation_message = (
                f"Subscription will be canceled at the end of your billing period"
                if request.at_period_end
                else "Subscription canceled immediately"
            )
            
            logger.info(f"Canceled subscription for user {user.id}")
            
            return {
                "success": True,
                "message": cancellation_message,
                "cancellation": result,
                "downgrade_date": result["canceled_at"].isoformat() if not request.at_period_end else None
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Subscription cancellation failed for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
    
    @cached(ttl=300, key_prefix="payment_methods")
    async def get_payment_methods(self, user: User) -> Dict[str, Any]:
        """
        Get user's payment methods.
        
        Args:
            user: Authenticated user
            
        Returns:
            List of payment methods
        """
        try:
            if not user.stripe_customer_id:
                return {
                    "payment_methods": [],
                    "message": "No customer ID found"
                }
            
            payment_methods = await self.stripe_service.get_customer_payment_methods(
                user.stripe_customer_id
            )
            
            return {
                "payment_methods": payment_methods,
                "count": len(payment_methods)
            }
            
        except Exception as e:
            logger.error(f"Failed to get payment methods for user {user.id}: {e}")
            return {
                "payment_methods": [],
                "error": "Failed to retrieve payment methods"
            }
    
    async def get_billing_portal_url(self, user: User) -> Dict[str, Any]:
        """
        Generate Stripe billing portal URL for customer self-service.
        
        Args:
            user: Authenticated user
            
        Returns:
            Billing portal URL
        """
        if not self.stripe_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Billing portal not available in development mode"
            )
        
        if not user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing account found"
            )
        
        try:
            # Create billing portal session
            import stripe
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url="https://your-domain.com/billing"  # Configure this
            )
            
            return {
                "url": session.url,
                "expires_at": datetime.fromtimestamp(session.created + 1800).isoformat()  # 30 minutes
            }
            
        except Exception as e:
            logger.error(f"Failed to create billing portal for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create billing portal session"
            )
    
    async def get_pricing_info(self) -> Dict[str, Any]:
        """
        Get pricing information for all tiers.
        
        Returns:
            Pricing details
        """
        pricing = self.stripe_service.pricing
        
        return {
            "tiers": {
                tier.value: {
                    "monthly_price_cents": config["monthly_price"],
                    "monthly_price_usd": config["monthly_price"] / 100,
                    "requests_included": config["requests_included"],
                    "overage_per_request_cents": config["overage_per_request"],
                    "overage_per_request_usd": config["overage_per_request"] / 100
                }
                for tier, config in pricing.items()
            },
            "free_tier": {
                "monthly_price_cents": 0,
                "monthly_price_usd": 0,
                "requests_included": 100,
                "overage_per_request_cents": None,
                "features": ["Basic signals", "Limited symbols"]
            },
            "currency": "USD"
        }


# Global handler instance
_billing_handler: Optional[BillingHandler] = None


def get_billing_handler() -> BillingHandler:
    """Get global billing handler instance."""
    global _billing_handler
    if _billing_handler is None:
        _billing_handler = BillingHandler()
    return _billing_handler