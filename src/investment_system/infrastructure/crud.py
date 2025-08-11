"""
CRUD operations for database models.
Secure database operations with validation.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func

from investment_system.infrastructure.database import (
    User, Subscription, APIUsage, Signal, MarketData, AuditLog
)
from investment_system.core.contracts import UserTier, SignalType
from investment_system.security.password import (
    generate_api_key, hash_api_key, verify_api_key,
    generate_secure_token
)


class UserCRUD:
    """CRUD operations for User model"""
    
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        tier: UserTier = UserTier.FREE
    ) -> User:
        """Create new user with secure defaults"""
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("User with this email already exists")
        
        # Generate API key
        api_key_id, api_key_secret = generate_api_key()
        
        # Create user
        user = User(
            email=email,
            tier=tier,
            api_key_id=api_key_id,
            api_key_hash=hash_api_key(api_key_secret),
            verification_token=generate_secure_token()
        )
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Return user with temporary API key (only shown once)
        user.temp_api_key = api_key_secret
        return user
    
    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_api_key(
        db: Session,
        api_key_id: str,
        api_key_secret: str
    ) -> Optional[User]:
        """Get user by API key"""
        user = db.query(User).filter(User.api_key_id == api_key_id).first()
        if user and verify_api_key(api_key_secret, user.api_key_hash):
            # Update last used timestamp
            user.api_key_last_used = datetime.utcnow()
            db.commit()
            return user
        return None
    
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user with password"""
        user = UserCRUD.get_user_by_email(db, email)
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return None
        
        # Verify password
        if not user.check_password(password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            
            db.commit()
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def update_user_tier(
        db: Session,
        user_id: uuid.UUID,
        new_tier: UserTier
    ) -> User:
        """Update user subscription tier"""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        user.tier = new_tier
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def rotate_api_key(
        db: Session,
        user_id: uuid.UUID
    ) -> tuple[str, str]:
        """Rotate user's API key"""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generate new API key
        api_key_id, api_key_secret = generate_api_key()
        
        # Update user
        user.api_key_id = api_key_id
        user.api_key_hash = hash_api_key(api_key_secret)
        user.api_key_created_at = datetime.utcnow()
        
        db.commit()
        
        return api_key_id, api_key_secret
    
    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID) -> bool:
        """Delete user and all related data"""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True


class SubscriptionCRUD:
    """CRUD operations for Subscription model"""
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: uuid.UUID,
        tier: UserTier,
        stripe_subscription_id: Optional[str] = None,
        amount: float = 0.0
    ) -> Subscription:
        """Create new subscription"""
        # Cancel existing active subscriptions
        db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).update({"status": "cancelled", "cancelled_at": datetime.utcnow()})
        
        # Create new subscription
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            stripe_subscription_id=stripe_subscription_id,
            amount=amount,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        # Set limits based on tier
        limits = {
            UserTier.FREE: (100, 5),
            UserTier.STARTER: (1000, 20),
            UserTier.PRO: (10000, 100),
            UserTier.ENTERPRISE: (100000, -1)
        }
        subscription.api_calls_limit, subscription.symbols_limit = limits.get(
            tier, (100, 5)
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def get_active_subscription(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[Subscription]:
        """Get user's active subscription"""
        return db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
    
    @staticmethod
    def cancel_subscription(
        db: Session,
        subscription_id: uuid.UUID
    ) -> Subscription:
        """Cancel subscription"""
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        subscription.expires_at = subscription.current_period_end
        
        db.commit()
        db.refresh(subscription)
        return subscription


class APIUsageCRUD:
    """CRUD operations for API usage tracking"""
    
    @staticmethod
    def track_usage(
        db: Session,
        user_id: uuid.UUID,
        endpoint: str,
        method: str,
        units: int = 1,
        status_code: int = 200,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> APIUsage:
        """Track API usage"""
        usage = APIUsage(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            units=units,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(usage)
        db.commit()
        db.refresh(usage)
        return usage
    
    @staticmethod
    def get_usage_stats(
        db: Session,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for user"""
        if not start_date:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Query usage data
        usage_query = db.query(APIUsage).filter(
            and_(
                APIUsage.user_id == user_id,
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            )
        )
        
        # Calculate stats
        total_calls = usage_query.count()
        total_units = db.query(func.sum(APIUsage.units)).filter(
            and_(
                APIUsage.user_id == user_id,
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            )
        ).scalar() or 0
        
        # Group by endpoint
        endpoint_stats = db.query(
            APIUsage.endpoint,
            func.count(APIUsage.id).label("calls"),
            func.sum(APIUsage.units).label("units")
        ).filter(
            and_(
                APIUsage.user_id == user_id,
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            )
        ).group_by(APIUsage.endpoint).all()
        
        return {
            "total_calls": total_calls,
            "total_units": total_units,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "by_endpoint": [
                {
                    "endpoint": stat.endpoint,
                    "calls": stat.calls,
                    "units": stat.units
                }
                for stat in endpoint_stats
            ]
        }
    
    @staticmethod
    def check_rate_limit(
        db: Session,
        user_id: uuid.UUID,
        window_minutes: int = 60
    ) -> tuple[bool, int]:
        """Check if user has exceeded rate limit"""
        # Get user's subscription limits
        subscription = SubscriptionCRUD.get_active_subscription(db, user_id)
        if not subscription:
            limit = 100  # Default free tier
        else:
            limit = subscription.api_calls_limit
        
        # Count recent calls
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_calls = db.query(APIUsage).filter(
            and_(
                APIUsage.user_id == user_id,
                APIUsage.created_at >= since
            )
        ).count()
        
        return recent_calls < limit, limit - recent_calls


class SignalCRUD:
    """CRUD operations for trading signals"""
    
    @staticmethod
    def create_signal(
        db: Session,
        user_id: uuid.UUID,
        symbol: str,
        signal_type: SignalType,
        confidence: float,
        price: float,
        indicators: Dict[str, Any],
        reasoning: Optional[str] = None,
        ai_enhanced: bool = False
    ) -> Signal:
        """Create new trading signal"""
        signal = Signal(
            user_id=user_id,
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            price=price,
            indicators=indicators,
            reasoning=reasoning,
            ai_enhanced=ai_enhanced,
            rsi=indicators.get("rsi"),
            sma_20=indicators.get("sma_20"),
            sma_50=indicators.get("sma_50"),
            volume=indicators.get("volume")
        )
        
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal
    
    @staticmethod
    def get_user_signals(
        db: Session,
        user_id: uuid.UUID,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Signal]:
        """Get user's signals"""
        query = db.query(Signal).filter(Signal.user_id == user_id)
        
        if symbol:
            query = query.filter(Signal.symbol == symbol)
        
        return query.order_by(Signal.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_signal_performance(
        db: Session,
        signal_id: uuid.UUID,
        exit_price: float
    ) -> Signal:
        """Update signal with performance metrics"""
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            raise ValueError("Signal not found")
        
        signal.exit_price = exit_price
        if signal.price:
            signal.profit_loss = exit_price - float(signal.price)
            signal.accuracy = 1.0 if (
                (signal.signal_type == SignalType.BUY and signal.profit_loss > 0) or
                (signal.signal_type == SignalType.SELL and signal.profit_loss < 0)
            ) else 0.0
        
        db.commit()
        db.refresh(signal)
        return signal


class AuditLogCRUD:
    """CRUD operations for audit logging"""
    
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        event_category: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_score: Optional[int] = None
    ) -> AuditLog:
        """Log security event"""
        log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            risk_score=risk_score,
            flagged=risk_score and risk_score > 70
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_flagged_events(
        db: Session,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get flagged security events"""
        return db.query(AuditLog).filter(
            AuditLog.flagged == True
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_user_events(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit events for user"""
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()