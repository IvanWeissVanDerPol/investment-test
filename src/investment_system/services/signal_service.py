"""
Signal generation service with caching and billing integration.
This is the core revenue-generating service.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

from investment_system.core.contracts import (
    MarketData, TradingSignal, SignalRequest, SignalResponse,
    UserTier, User, RateLimitStatus, ErrorCode, ErrorResponse
)
from investment_system.core.analyzers import AnalyzerFactory, BaseAnalyzer
from investment_system.infrastructure.cache import get_cache, cache_result
from investment_system.pipeline.ingest import fetch_prices
from investment_system.pipeline.analyze import generate_signals as legacy_generate_signals
# Integration with new repository pattern and monitoring
from investment_system.repositories.signal_repository import SignalRepository
from investment_system.repositories.user_repository import UserRepository
from investment_system.core.logging import get_logger
from investment_system.core.monitoring import track_custom_metric, increment_counter
from investment_system.infrastructure.database_session import get_database_session

logger = get_logger(__name__)


class SignalService:
    """Service for generating trading signals with repository pattern integration"""
    
    def __init__(self, signal_repository: Optional[SignalRepository] = None, user_repository: Optional[UserRepository] = None):
        # Existing sophisticated features
        self.cache = get_cache()
        self.analyzer_factory = AnalyzerFactory()
        self._ai_hooks = {}
        
        # New repository pattern integration (optional for backward compatibility)
        self.signal_repository = signal_repository
        self.user_repository = user_repository
        
        logger.info("SignalService initialized", has_repositories=bool(signal_repository and user_repository))
        
    def register_ai_hook(self, hook_name: str, handler: callable):
        """Register an AI hook for signal enhancement"""
        self._ai_hooks[hook_name] = handler
    
    async def generate_signals(
        self,
        request: SignalRequest,
        user: User
    ) -> SignalResponse:
        """
        Generate trading signals for requested symbols.
        This is the main revenue-generating endpoint.
        Enhanced with repository pattern for persistence.
        """
        request_id = str(uuid.uuid4())
        
        # Track signal generation metrics
        increment_counter("signal_requests_total")
        track_custom_metric("signal_request_symbols_count", len(request.symbols))
        
        logger.info(
            "Signal generation started",
            request_id=request_id,
            user_tier=user.tier.value,
            symbols=request.symbols,
            ai_hooks_registered=len(self._ai_hooks)
        )
        
        # Check user limits
        if not self._check_user_limits(user, request):
            raise ValueError(ErrorCode.SUBSCRIPTION_REQUIRED)
        
        # Try cache first (different cache for different tiers)
        cached_signals = self._get_cached_signals(request.symbols, user.tier)
        if cached_signals:
            return SignalResponse(
                signals=cached_signals,
                request_id=request_id,
                cached=True,
                rate_limit=self._get_rate_limit_status(user)
            )
        
        # Fetch market data
        market_data_list = await self._fetch_market_data(
            request.symbols,
            request.lookback_days
        )
        
        # Generate signals with enhanced repository integration
        signals = []
        for market_data in market_data_list:
            signal = await self._generate_signal_for_symbol(
                market_data,
                user.tier,
                request.indicators
            )
            signals.append(signal)
            
            # Persist signal to repository if available
            if self.signal_repository:
                try:
                    await self._persist_signal(signal, user.id, request_id)
                except Exception as e:
                    logger.warning("Failed to persist signal to repository", error=str(e), symbol=signal.symbol)
        
        # Cache results
        self._cache_signals(request.symbols, user.tier, signals)
        
        # Track usage for billing
        await self._track_usage(user, request.symbols)
        
        # Update metrics
        increment_counter("signals_generated_total", len(signals))
        track_custom_metric("signal_generation_success", 1)
        
        logger.info(
            "Signal generation completed",
            request_id=request_id,
            signals_count=len(signals),
            cached=False,
            ai_enhanced=any(getattr(s, 'ai_enhanced', False) for s in signals)
        )
        
        return SignalResponse(
            signals=signals,
            request_id=request_id,
            cached=False,
            rate_limit=self._get_rate_limit_status(user)
        )
    
    def _check_user_limits(self, user: User, request: SignalRequest) -> bool:
        """Check if user can make this request"""
        limits = user.tier_limits
        
        # Check symbol limit
        if limits['symbols'] != -1 and len(request.symbols) > limits['symbols']:
            return False
        
        # Check daily signal limit (would need to query DB for actual count)
        # For now, always allow if not free tier
        if user.tier == UserTier.FREE and len(request.symbols) > 5:
            return False
        
        return True
    
    def _get_cached_signals(
        self,
        symbols: List[str],
        tier: UserTier
    ) -> Optional[List[TradingSignal]]:
        """Get signals from cache if available"""
        return self.cache.get_signals(symbols, tier.value)
    
    def _cache_signals(
        self,
        symbols: List[str],
        tier: UserTier,
        signals: List[TradingSignal]
    ):
        """Cache generated signals"""
        self.cache.set_signals(symbols, tier.value, signals)
    
    async def _fetch_market_data(
        self,
        symbols: List[str],
        lookback_days: int
    ) -> List[MarketData]:
        """Fetch market data for symbols"""
        # Use the existing pipeline function
        df = fetch_prices(symbols, lookback_days)
        
        # Convert to MarketData objects
        market_data_list = []
        for symbol in symbols:
            symbol_df = df[df['symbol'] == symbol]
            if symbol_df.empty:
                continue
            
            prices = []
            for _, row in symbol_df.iterrows():
                from investment_system.core.contracts import PricePoint
                prices.append(PricePoint(
                    timestamp=row['date'],
                    open=Decimal(str(row['open'])),
                    high=Decimal(str(row['high'])),
                    low=Decimal(str(row['low'])),
                    close=Decimal(str(row['close'])),
                    volume=int(row['volume'])
                ))
            
            market_data = MarketData(
                symbol=symbol,
                prices=prices,
                is_stale=symbol_df['is_stale'].iloc[0] if 'is_stale' in symbol_df else False
            )
            market_data_list.append(market_data)
        
        return market_data_list
    
    async def _generate_signal_for_symbol(
        self,
        market_data: MarketData,
        tier: UserTier,
        indicators: Optional[List] = None
    ) -> TradingSignal:
        """Generate signal for a single symbol"""
        
        # Select analyzer based on tier
        if tier == UserTier.ENTERPRISE:
            analyzer = self.analyzer_factory.create("ai_enhanced")
        elif tier == UserTier.PRO:
            analyzer = self.analyzer_factory.create("momentum")
        else:
            analyzer = self.analyzer_factory.create("technical")
        
        # Register AI hooks if available
        if self._ai_hooks:
            for hook_name, handler in self._ai_hooks.items():
                analyzer.hooks.register(hook_name, handler)
        
        # Generate signal
        signal = analyzer.analyze(market_data)
        
        # Add tier-specific enhancements
        if tier in [UserTier.PRO, UserTier.ENTERPRISE]:
            signal.reasoning = self._generate_reasoning(signal)
        
        return signal
    
    def _generate_reasoning(self, signal: TradingSignal) -> str:
        """Generate human-readable reasoning for signal"""
        reasons = []
        
        if signal.signal == "buy":
            reasons.append("Bullish signal detected")
            if signal.indicators.get("rsi", 50) < 30:
                reasons.append("RSI indicates oversold condition")
            if signal.indicators.get("sma_20", 0) > signal.indicators.get("sma_50", 0):
                reasons.append("Golden cross pattern (bullish momentum)")
        elif signal.signal == "sell":
            reasons.append("Bearish signal detected")
            if signal.indicators.get("rsi", 50) > 70:
                reasons.append("RSI indicates overbought condition")
            if signal.indicators.get("sma_20", 0) < signal.indicators.get("sma_50", 0):
                reasons.append("Death cross pattern (bearish momentum)")
        else:
            reasons.append("Neutral market conditions")
            reasons.append("No clear directional signal")
        
        reasons.append(f"Confidence level: {signal.confidence:.1%}")
        
        return " | ".join(reasons)
    
    async def _track_usage(self, user: User, symbols: List[str]):
        """Track API usage for billing"""
        # This would integrate with billing service
        # For MVP, just log it
        from investment_system.core.contracts import APIUsage
        usage = APIUsage(
            user_id=user.id,
            endpoint="/signals",
            method="GET",
            units=len(symbols),
            status_code=200
        )
        # In production, save to database
        print(f"Usage tracked: {user.id} used {len(symbols)} symbol queries")
    
    async def _persist_signal(self, signal: TradingSignal, user_id: str, request_id: str) -> None:
        """Persist signal to repository with enhanced metadata."""
        if not self.signal_repository:
            return
        
        try:
            # Convert TradingSignal to repository format
            signal_data = {
                "symbol": signal.symbol,
                "signal_type": signal.signal,
                "timestamp": datetime.utcnow(),
                "confidence": signal.confidence,
                "price": float(signal.price) if signal.price else None,
                "user_id": user_id,
                "metadata": {
                    "request_id": request_id,
                    "indicators": signal.indicators,
                    "reasoning": getattr(signal, 'reasoning', None),
                    "ai_enhanced": getattr(signal, 'ai_enhanced', False),
                    "ai_hooks_used": list(self._ai_hooks.keys()) if self._ai_hooks else []
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Create signal using repository
            await self.signal_repository.create(signal_data)
            
            logger.debug(
                "Signal persisted to repository",
                symbol=signal.symbol,
                user_id=user_id,
                request_id=request_id,
                ai_enhanced=signal_data["metadata"]["ai_enhanced"]
            )
            
        except Exception as e:
            logger.error(
                "Failed to persist signal",
                error=str(e),
                symbol=signal.symbol,
                user_id=user_id
            )
            # Don't fail the entire request if persistence fails
            increment_counter("signal_persistence_failures")
    
    def _get_rate_limit_status(self, user: User) -> RateLimitStatus:
        """Get current rate limit status for user"""
        limits = user.tier_limits
        
        # In production, query actual usage from database
        # For MVP, return mock data
        return RateLimitStatus(
            limit=limits['api_calls'],
            remaining=max(0, limits['api_calls'] - 10),  # Mock: used 10 calls
            reset_at=datetime.utcnow().replace(hour=23, minute=59, second=59),
            tier=user.tier
        )
    
    async def get_signal_history(
        self,
        symbol: str,
        user: User,
        days: int = 7
    ) -> List[TradingSignal]:
        """Get historical signals for a symbol (premium feature)"""
        if user.tier == UserTier.FREE:
            raise ValueError(ErrorCode.SUBSCRIPTION_REQUIRED)
        
        # In production, query from database
        # For MVP, return empty list
        return []
    
    async def get_portfolio_signals(
        self,
        user: User,
        portfolio: List[Dict[str, Any]]
    ) -> List[TradingSignal]:
        """Generate signals for entire portfolio (premium feature)"""
        if user.tier not in [UserTier.PRO, UserTier.ENTERPRISE]:
            raise ValueError(ErrorCode.SUBSCRIPTION_REQUIRED)
        
        symbols = [holding['symbol'] for holding in portfolio]
        request = SignalRequest(symbols=symbols)
        
        response = await self.generate_signals(request, user)
        return response.signals


class SignalAggregator:
    """Aggregate signals from multiple sources (future feature)"""
    
    def __init__(self):
        self.sources = []
    
    def add_source(self, source: BaseAnalyzer, weight: float = 1.0):
        """Add a signal source with weight"""
        self.sources.append((source, weight))
    
    def aggregate(self, market_data: MarketData) -> TradingSignal:
        """Aggregate signals from all sources"""
        if not self.sources:
            raise ValueError("No signal sources configured")
        
        signals = []
        weights = []
        
        for source, weight in self.sources:
            signal = source.analyze(market_data)
            signals.append(signal)
            weights.append(weight)
        
        # Weighted average of confidence
        total_weight = sum(weights)
        weighted_confidence = sum(
            s.confidence * w for s, w in zip(signals, weights)
        ) / total_weight
        
        # Majority vote for signal type
        signal_votes = {}
        for signal, weight in zip(signals, weights):
            signal_votes[signal.signal] = signal_votes.get(signal.signal, 0) + weight
        
        final_signal_type = max(signal_votes, key=signal_votes.get)
        
        # Average indicators
        all_indicators = {}
        for signal in signals:
            for indicator, value in signal.indicators.items():
                if indicator not in all_indicators:
                    all_indicators[indicator] = []
                all_indicators[indicator].append(value)
        
        avg_indicators = {
            k: sum(v) / len(v) for k, v in all_indicators.items()
        }
        
        # Create aggregated signal
        return TradingSignal(
            symbol=market_data.symbol,
            signal=final_signal_type,
            confidence=weighted_confidence,
            price=market_data.latest_price,
            indicators=avg_indicators,
            reasoning=f"Aggregated from {len(self.sources)} sources",
            ai_enhanced=any(s.ai_enhanced for s in signals)
        )


# Global service instance
_signal_service: Optional[SignalService] = None


def get_signal_service() -> SignalService:
    """Get global signal service instance"""
    global _signal_service
    if _signal_service is None:
        _signal_service = SignalService()
    return _signal_service