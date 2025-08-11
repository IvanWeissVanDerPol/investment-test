"""
Signal generation handlers with caching and resilience.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
import logging

from investment_system.cache import get_cache, cached
from investment_system.utils.resilience import (
    retry_with_backoff,
    with_circuit_breaker,
    with_recovery,
    FallbackRecovery
)
from investment_system.core.contracts import SignalRequest, TradingSignal
from investment_system.analysis.signal_generator import SignalGenerator

logger = logging.getLogger(__name__)


class SignalHandler:
    """Handles signal generation with caching and resilience."""
    
    def __init__(self):
        self.cache = get_cache()
        self.generator = SignalGenerator()
    
    @cached(ttl=600, key_prefix="signals")
    @retry_with_backoff(retries=3, backoff_in_seconds=1.0)
    @with_circuit_breaker("market_data")
    async def get_signals(
        self,
        request: SignalRequest,
        use_cache: bool = True
    ) -> List[TradingSignal]:
        """
        Generate trading signals with caching and resilience.
        
        Args:
            request: Signal generation request
            use_cache: Whether to use cached results
            
        Returns:
            List of trading signals
        """
        try:
            # Generate cache key
            cache_key = f"signals:{':'.join(request.symbols)}:{request.lookback_days}"
            
            # Check cache if enabled
            if use_cache:
                cached_signals = self.cache.get(cache_key)
                if cached_signals:
                    logger.info(f"Cache hit for signals: {cache_key}")
                    return cached_signals
            
            # Generate new signals
            logger.info(f"Generating signals for {request.symbols}")
            signals = await self.generator.generate_signals(
                symbols=request.symbols,
                lookback_days=request.lookback_days
            )
            
            # Cache results
            if signals:
                self.cache.set(
                    cache_key,
                    signals,
                    ttl=600  # 10 minutes
                )
            
            return signals
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            
            # Try to return stale cached data as fallback
            stale_key = f"signals:stale:{':'.join(request.symbols)}"
            stale_signals = self.cache.get(stale_key)
            if stale_signals:
                logger.warning("Returning stale cached signals due to error")
                return stale_signals
            
            raise HTTPException(
                status_code=503,
                detail="Signal generation temporarily unavailable"
            )
    
    @retry_with_backoff(retries=2)
    async def get_latest_signals(
        self,
        symbol: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get latest signals from database.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of signals
            
        Returns:
            List of signal dictionaries
        """
        cache_key = f"latest_signals:{symbol or 'all'}:{limit}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query database
        from investment_system.db.store import get_store
        store = get_store()
        
        signals = await store.get_latest_signals(
            symbol=symbol,
            limit=limit
        )
        
        # Convert to dict format
        signal_dicts = [
            {
                "symbol": s.symbol,
                "timestamp": s.timestamp.isoformat(),
                "signal": s.signal,
                "confidence": s.confidence,
                "rsi": s.indicators.get("rsi"),
                "sma_20": s.indicators.get("sma_20"),
                "sma_50": s.indicators.get("sma_50")
            }
            for s in signals
        ]
        
        # Cache for 1 minute
        self.cache.set(cache_key, signal_dicts, ttl=60)
        
        return signal_dicts
    
    async def invalidate_signal_cache(self, symbols: Optional[List[str]] = None):
        """
        Invalidate signal cache.
        
        Args:
            symbols: Optional list of symbols to invalidate
        """
        if symbols:
            for symbol in symbols:
                pattern = f"signals:*{symbol}*"
                count = self.cache.clear_pattern(pattern)
                logger.info(f"Invalidated {count} cache entries for {symbol}")
        else:
            count = self.cache.clear_pattern("signals:*")
            logger.info(f"Invalidated {count} signal cache entries")
    
    @with_recovery(FallbackRecovery({"status": "degraded", "message": "Using fallback mode"}))
    async def get_signal_stats(self) -> Dict[str, Any]:
        """
        Get signal generation statistics.
        
        Returns:
            Statistics dictionary
        """
        cache_stats = self.cache.get_stats()
        
        return {
            "cache_stats": cache_stats,
            "total_signals_cached": cache_stats.get("memory_items", 0),
            "redis_connected": cache_stats.get("redis_connected", False),
            "last_updated": datetime.now().isoformat()
        }


# Global handler instance
_signal_handler: Optional[SignalHandler] = None


def get_signal_handler() -> SignalHandler:
    """Get global signal handler instance."""
    global _signal_handler
    if _signal_handler is None:
        _signal_handler = SignalHandler()
    return _signal_handler