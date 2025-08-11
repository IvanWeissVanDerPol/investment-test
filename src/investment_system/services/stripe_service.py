"""
Stripe payment processing service.
Handles subscriptions, billing, and payment methods.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

import stripe
from stripe.error import StripeError

from investment_system.core.contracts import User, UserTier
from investment_system.utils.resilience import (
    retry_with_backoff,
    with_circuit_breaker,
    with_recovery,
    FallbackRecovery
)
from investment_system.cache import cached

logger = logging.getLogger(__name__)


class StripeService:
    """
    Stripe payment processing service with resilience and caching.
    Handles all payment-related operations.
    """
    
    def __init__(self):
        """Initialize Stripe service with configuration."""
        # Get Stripe keys from environment
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not self.secret_key:
            logger.warning("STRIPE_SECRET_KEY not set, Stripe functionality disabled")
            self._enabled = False
            return
        
        # Configure Stripe
        stripe.api_key = self.secret_key
        self._enabled = True
        
        # Pricing configuration (in cents)
        self.pricing = {
            UserTier.STARTER: {
                "monthly_price": 2900,  # $29/month
                "price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
                "requests_included": 1000,
                "overage_per_request": 3  # 3 cents per request
            },
            UserTier.PRO: {
                "monthly_price": 9900,  # $99/month
                "price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
                "requests_included": 10000,
                "overage_per_request": 2  # 2 cents per request
            },
            UserTier.ENTERPRISE: {
                "monthly_price": 49900,  # $499/month
                "price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
                "requests_included": 100000,
                "overage_per_request": 1  # 1 cent per request
            }
        }
        
        logger.info("Stripe service initialized successfully")
    
    @property
    def enabled(self) -> bool:
        """Check if Stripe is enabled and configured."""
        return self._enabled
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    @with_circuit_breaker("stripe")
    async def create_customer(
        self,
        user: User,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer for a user.
        
        Args:
            user: User object
            payment_method_id: Optional payment method to attach
            
        Returns:
            Customer data dictionary
        """
        if not self.enabled:
            raise ValueError("Stripe not configured")
        
        try:
            # Create customer
            customer_data = {
                "email": user.email,
                "metadata": {
                    "user_id": user.id,
                    "tier": user.tier.value
                }
            }
            
            if payment_method_id:
                customer_data["payment_method"] = payment_method_id
                customer_data["invoice_settings"] = {
                    "default_payment_method": payment_method_id
                }
            
            customer = stripe.Customer.create(**customer_data)
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            
            return {
                "customer_id": customer.id,
                "email": customer.email,
                "created": datetime.fromtimestamp(customer.created),
                "payment_methods": len(customer.get("sources", {}).get("data", [])),
                "metadata": customer.metadata
            }
            
        except StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise ValueError(f"Payment processing error: {e.user_message or str(e)}")
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    @with_circuit_breaker("stripe")
    async def create_subscription(
        self,
        customer_id: str,
        tier: UserTier,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            tier: Subscription tier
            payment_method_id: Payment method to use
            
        Returns:
            Subscription data dictionary
        """
        if not self.enabled:
            raise ValueError("Stripe not configured")
        
        if tier not in self.pricing:
            raise ValueError(f"Invalid tier: {tier}")
        
        try:
            pricing_config = self.pricing[tier]
            price_id = pricing_config["price_id"]
            
            if not price_id:
                raise ValueError(f"Price ID not configured for tier {tier}")
            
            # Create subscription
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": {
                    "tier": tier.value,
                    "requests_included": pricing_config["requests_included"]
                },
                "billing_cycle_anchor": int((datetime.utcnow() + timedelta(days=1)).timestamp()),
                "proration_behavior": "always_invoice"
            }
            
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            
            return {
                "subscription_id": subscription.id,
                "customer_id": customer_id,
                "status": subscription.status,
                "tier": tier,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "monthly_price": pricing_config["monthly_price"],
                "requests_included": pricing_config["requests_included"],
                "next_invoice": datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise ValueError(f"Subscription creation error: {e.user_message or str(e)}")
    
    @cached(ttl=300, key_prefix="stripe_subscription")
    @retry_with_backoff(retries=2, backoff_in_seconds=0.5)
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription data dictionary
        """
        if not self.enabled:
            raise ValueError("Stripe not configured")
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "subscription_id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                "metadata": subscription.metadata
            }
            
        except StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise ValueError(f"Subscription retrieval error: {e.user_message or str(e)}")
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            Updated subscription data
        """
        if not self.enabled:
            raise ValueError("Stripe not configured")
        
        try:
            if at_period_end:
                # Cancel at period end
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Canceled subscription {subscription_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise ValueError(f"Subscription cancellation error: {e.user_message or str(e)}")
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    async def create_usage_record(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a usage record for metered billing.
        
        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity (e.g., number of API requests)
            timestamp: Usage timestamp (defaults to now)
            
        Returns:
            Usage record data
        """
        if not self.enabled:
            raise ValueError("Stripe not configured")
        
        try:
            usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                quantity=quantity,
                timestamp=int((timestamp or datetime.utcnow()).timestamp()),
                action="increment"
            )
            
            return {
                "id": usage_record.id,
                "quantity": usage_record.quantity,
                "timestamp": datetime.fromtimestamp(usage_record.timestamp),
                "subscription_item": usage_record.subscription_item
            }
            
        except StripeError as e:
            logger.error(f"Failed to create usage record: {e}")
            raise ValueError(f"Usage tracking error: {e.user_message or str(e)}")
    
    async def calculate_overage_charges(
        self,
        user: User,
        current_usage: int,
        billing_period_start: datetime
    ) -> Dict[str, Any]:
        """
        Calculate overage charges for a user.
        
        Args:
            user: User object
            current_usage: Current API usage count
            billing_period_start: Start of billing period
            
        Returns:
            Overage calculation
        """
        if user.tier not in self.pricing:
            return {"overage": 0, "overage_requests": 0}
        
        pricing_config = self.pricing[user.tier]
        included_requests = pricing_config["requests_included"]
        overage_rate = pricing_config["overage_per_request"]
        
        if current_usage <= included_requests:
            return {
                "overage": 0,
                "overage_requests": 0,
                "included_requests": included_requests,
                "current_usage": current_usage,
                "remaining": included_requests - current_usage
            }
        
        overage_requests = current_usage - included_requests
        overage_amount = overage_requests * overage_rate
        
        return {
            "overage": overage_amount,
            "overage_requests": overage_requests,
            "included_requests": included_requests,
            "current_usage": current_usage,
            "overage_rate_cents": overage_rate,
            "remaining": 0
        }
    
    async def get_customer_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer's payment methods.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of payment methods
        """
        if not self.enabled:
            return []
        
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            return [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year
                    },
                    "created": datetime.fromtimestamp(pm.created)
                }
                for pm in payment_methods.data
            ]
            
        except StripeError as e:
            logger.error(f"Failed to get payment methods for {customer_id}: {e}")
            return []
    
    def construct_webhook_event(self, payload: bytes, sig_header: str) -> Any:
        """
        Construct and verify webhook event.
        
        Args:
            payload: Request payload
            sig_header: Stripe signature header
            
        Returns:
            Stripe event object
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")
        
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise


# Global service instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get global Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service