"""
Enhanced Real-time Data Manager
Handles WebSocket connections, data streaming, and real-time market updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import redis
from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from .market_data_collector import MarketDataCollector
from ..utils.secure_config_manager import get_config_manager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MarketUpdate:
    """Real-time market data update"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    source: str = "real_time"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


@dataclass
class PortfolioUpdate:
    """Real-time portfolio update"""
    user_id: str
    total_value: float
    daily_change: float
    daily_change_percent: float
    positions: List[Dict[str, Any]]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'total_value': self.total_value,
            'daily_change': self.daily_change,
            'daily_change_percent': self.daily_change_percent,
            'positions': self.positions,
            'timestamp': self.timestamp.isoformat()
        }


class RealTimeDataManager:
    """
    Manages real-time data streams, WebSocket connections, and live updates
    """
    
    def __init__(self, socketio: SocketIO):
        """Initialize real-time data manager"""
        self.socketio = socketio
        self.config = get_config_manager()
        self.audit_logger = get_audit_logger()
        self.market_collector = MarketDataCollector()
        
        # Redis for caching and pub/sub
        try:
            redis_url = get_settings().redis.redis_url
            self.redis_client = redis.from_url(redis_url)
            self.redis_pubsub = self.redis_client.pubsub()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
            self.redis_pubsub = None
        
        # Connection tracking
        self.connected_users: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.user_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> symbols
        self.symbol_subscribers: Dict[str, Set[str]] = defaultdict(set)  # symbol -> user_ids
        
        # Rate limiting
        self.user_request_counts: Dict[str, List[datetime]] = defaultdict(list)
        self.max_requests_per_minute = 60
        
        # Data update tracking
        self.last_market_update: Dict[str, datetime] = {}  # symbol -> last_update_time
        self.update_interval = 30  # seconds between updates
        
        # Background tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self.update_thread = None
        
        # Register WebSocket event handlers
        self._register_websocket_handlers()
    
    def _register_websocket_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle new WebSocket connection"""
            try:
                # Verify authentication (handled in main app)
                session_id = request.sid
                user_id = session.get('user_id')
                
                if not user_id:
                    logger.warning("Unauthenticated WebSocket connection attempt")
                    return False
                
                # Add to connection tracking
                self.connected_users[user_id].add(session_id)
                
                # Join user-specific room
                join_room(f"user_{user_id}")
                
                # Send welcome message
                emit('connected', {
                    'status': 'connected',
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Audit log
                self.audit_logger.log_event(
                    EventType.API_CALL,
                    SeverityLevel.LOW,
                    user_id=user_id,
                    resource='websocket',
                    action='connect',
                    details={'session_id': session_id}
                )
                
                logger.info(f"WebSocket connected: user={user_id}, session={session_id}")
                
            except Exception as e:
                logger.error(f"WebSocket connect error: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection"""
            try:
                session_id = request.sid
                user_id = session.get('user_id')
                
                if user_id:
                    # Remove from connection tracking
                    self.connected_users[user_id].discard(session_id)
                    if not self.connected_users[user_id]:
                        del self.connected_users[user_id]
                        # Unsubscribe from all symbols
                        for symbol in list(self.user_subscriptions[user_id]):
                            self._unsubscribe_symbol(user_id, symbol)
                    
                    # Leave user room
                    leave_room(f"user_{user_id}")
                    
                    # Audit log
                    self.audit_logger.log_event(
                        EventType.API_CALL,
                        SeverityLevel.LOW,
                        user_id=user_id,
                        resource='websocket',
                        action='disconnect',
                        details={'session_id': session_id}
                    )
                    
                    logger.info(f"WebSocket disconnected: user={user_id}, session={session_id}")
                    
            except Exception as e:
                logger.error(f"WebSocket disconnect error: {e}")
        
        @self.socketio.on('subscribe_symbols')
        def handle_subscribe_symbols(data):
            """Handle symbol subscription"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                # Rate limiting
                if not self._check_rate_limit(user_id):
                    emit('error', {'message': 'Rate limit exceeded'})
                    return
                
                symbols = data.get('symbols', [])
                if not isinstance(symbols, list) or not symbols:
                    emit('error', {'message': 'Invalid symbols list'})
                    return
                
                # Validate symbols
                valid_symbols = []
                for symbol in symbols[:20]:  # Limit to 20 symbols
                    if isinstance(symbol, str) and symbol.strip():
                        valid_symbols.append(symbol.strip().upper())
                
                # Subscribe to symbols
                for symbol in valid_symbols:
                    self._subscribe_symbol(user_id, symbol)
                
                emit('subscribed', {
                    'symbols': valid_symbols,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Send current data for subscribed symbols
                self._send_current_data(user_id, valid_symbols)
                
            except Exception as e:
                logger.error(f"Subscribe symbols error: {e}")
                emit('error', {'message': 'Subscription failed'})
        
        @self.socketio.on('unsubscribe_symbols')
        def handle_unsubscribe_symbols(data):
            """Handle symbol unsubscription"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                symbols = data.get('symbols', [])
                if not isinstance(symbols, list):
                    emit('error', {'message': 'Invalid symbols list'})
                    return
                
                # Unsubscribe from symbols
                for symbol in symbols:
                    if isinstance(symbol, str):
                        self._unsubscribe_symbol(user_id, symbol.strip().upper())
                
                emit('unsubscribed', {
                    'symbols': symbols,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Unsubscribe symbols error: {e}")
                emit('error', {'message': 'Unsubscription failed'})
        
        @self.socketio.on('request_portfolio_update')
        def handle_portfolio_update():
            """Handle portfolio update request"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                # Rate limiting
                if not self._check_rate_limit(user_id):
                    emit('error', {'message': 'Rate limit exceeded'})
                    return
                
                # Get and send portfolio update
                portfolio_update = self._get_portfolio_update(user_id)
                if portfolio_update:
                    emit('portfolio_update', portfolio_update.to_dict())
                
            except Exception as e:
                logger.error(f"Portfolio update error: {e}")
                emit('error', {'message': 'Portfolio update failed'})
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.user_request_counts[user_id] = [
            req_time for req_time in self.user_request_counts[user_id]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.user_request_counts[user_id]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self.user_request_counts[user_id].append(now)
        return True
    
    def _subscribe_symbol(self, user_id: str, symbol: str):
        """Subscribe user to symbol updates"""
        self.user_subscriptions[user_id].add(symbol)
        self.symbol_subscribers[symbol].add(user_id)
        
        # Subscribe to Redis channel if available
        if self.redis_pubsub:
            try:
                self.redis_pubsub.subscribe(f"market_data:{symbol}")
            except Exception as e:
                logger.error(f"Redis subscription error: {e}")
    
    def _unsubscribe_symbol(self, user_id: str, symbol: str):
        """Unsubscribe user from symbol updates"""
        self.user_subscriptions[user_id].discard(symbol)
        self.symbol_subscribers[symbol].discard(user_id)
        
        # Clean up empty sets
        if not self.symbol_subscribers[symbol]:
            del self.symbol_subscribers[symbol]
            
            # Unsubscribe from Redis channel if no more subscribers
            if self.redis_pubsub:
                try:
                    self.redis_pubsub.unsubscribe(f"market_data:{symbol}")
                except Exception as e:
                    logger.error(f"Redis unsubscription error: {e}")
    
    def _send_current_data(self, user_id: str, symbols: List[str]):
        """Send current market data for symbols"""
        try:
            for symbol in symbols:
                # Get cached data first
                cached_data = self._get_cached_market_data(symbol)
                if cached_data:
                    self.socketio.emit(
                        'market_update',
                        cached_data,
                        room=f"user_{user_id}"
                    )
                else:
                    # Fetch fresh data asynchronously
                    self.executor.submit(self._fetch_and_send_data, user_id, symbol)
                    
        except Exception as e:
            logger.error(f"Send current data error: {e}")
    
    def _get_cached_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached market data from Redis"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(f"market_data:{symbol}")
            if cached:
                data = json.loads(cached)
                return data
        except Exception as e:
            logger.error(f"Redis cache error: {e}")
        
        return None
    
    def _cache_market_data(self, symbol: str, data: Dict[str, Any], ttl: int = 60):
        """Cache market data in Redis"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                f"market_data:{symbol}",
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Redis cache write error: {e}")
    
    def _fetch_and_send_data(self, user_id: str, symbol: str):
        """Fetch fresh market data and send to user"""
        try:
            # Get fresh market data
            stock_data = self.market_collector.get_real_time_quote(symbol)
            if stock_data:
                market_update = MarketUpdate(
                    symbol=symbol,
                    price=stock_data.get('price', 0),
                    change=stock_data.get('change', 0),
                    change_percent=stock_data.get('change_percent', 0),
                    volume=stock_data.get('volume', 0),
                    timestamp=datetime.utcnow()
                )
                
                update_data = market_update.to_dict()
                
                # Cache the data
                self._cache_market_data(symbol, update_data)
                
                # Send to user
                self.socketio.emit(
                    'market_update',
                    update_data,
                    room=f"user_{user_id}"
                )
                
        except Exception as e:
            logger.error(f"Fetch and send data error for {symbol}: {e}")
    
    def _get_portfolio_update(self, user_id: str) -> Optional[PortfolioUpdate]:
        """Get portfolio update for user"""
        try:
            # This would integrate with your portfolio service
            # For now, return mock data
            portfolio_update = PortfolioUpdate(
                user_id=user_id,
                total_value=10000.0,
                daily_change=250.50,
                daily_change_percent=2.56,
                positions=[
                    {
                        'symbol': 'NVDA',
                        'quantity': 10,
                        'value': 5000.0,
                        'change': 125.0,
                        'change_percent': 2.56
                    }
                ],
                timestamp=datetime.utcnow()
            )
            
            return portfolio_update
            
        except Exception as e:
            logger.error(f"Portfolio update error: {e}")
            return None
    
    def start_background_updates(self):
        """Start background data update process"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._background_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("Real-time data updates started")
    
    def stop_background_updates(self):
        """Stop background data update process"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        logger.info("Real-time data updates stopped")
    
    def _background_update_loop(self):
        """Background loop for market data updates"""
        while self.running:
            try:
                # Get all symbols that have subscribers
                symbols_to_update = list(self.symbol_subscribers.keys())
                
                if symbols_to_update:
                    # Update market data for subscribed symbols
                    for symbol in symbols_to_update:
                        if not self.running:
                            break
                        
                        try:
                            self._update_symbol_data(symbol)
                            time.sleep(1)  # Small delay between symbol updates
                        except Exception as e:
                            logger.error(f"Symbol update error for {symbol}: {e}")
                
                # Sleep until next update cycle
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Background update loop error: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _update_symbol_data(self, symbol: str):
        """Update market data for a specific symbol"""
        now = datetime.utcnow()
        last_update = self.last_market_update.get(symbol)
        
        # Check if we need to update (respect rate limits)
        if last_update and (now - last_update).seconds < self.update_interval:
            return
        
        try:
            # Get fresh market data
            stock_data = self.market_collector.get_real_time_quote(symbol)
            if stock_data:
                market_update = MarketUpdate(
                    symbol=symbol,
                    price=stock_data.get('price', 0),
                    change=stock_data.get('change', 0),
                    change_percent=stock_data.get('change_percent', 0),
                    volume=stock_data.get('volume', 0),
                    timestamp=now
                )
                
                update_data = market_update.to_dict()
                
                # Cache the data
                self._cache_market_data(symbol, update_data)
                
                # Publish to Redis if available
                if self.redis_client:
                    try:
                        self.redis_client.publish(
                            f"market_data:{symbol}",
                            json.dumps(update_data)
                        )
                    except Exception as e:
                        logger.error(f"Redis publish error: {e}")
                
                # Send to all subscribers
                subscribers = self.symbol_subscribers.get(symbol, set())
                for user_id in subscribers:
                    try:
                        self.socketio.emit(
                            'market_update',
                            update_data,
                            room=f"user_{user_id}"
                        )
                    except Exception as e:
                        logger.error(f"WebSocket emit error: {e}")
                
                self.last_market_update[symbol] = now
                
        except Exception as e:
            logger.error(f"Market data update error for {symbol}: {e}")
    
    def broadcast_system_alert(self, message: str, severity: str = 'info'):
        """Broadcast system alert to all connected users"""
        try:
            alert_data = {
                'type': 'system_alert',
                'message': message,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('system_alert', alert_data, broadcast=True)
            
            # Audit log
            self.audit_logger.log_event(
                EventType.API_CALL,
                SeverityLevel.MEDIUM,
                resource='websocket',
                action='system_alert',
                details={'message': message, 'severity': severity}
            )
            
        except Exception as e:
            logger.error(f"System alert broadcast error: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get real-time connection statistics"""
        return {
            'connected_users': len(self.connected_users),
            'total_sessions': sum(len(sessions) for sessions in self.connected_users.values()),
            'subscribed_symbols': len(self.symbol_subscribers),
            'total_subscriptions': sum(len(subs) for subs in self.user_subscriptions.values()),
            'active_symbols': [symbol for symbol, subs in self.symbol_subscribers.items() if subs],
            'redis_connected': self.redis_client is not None,
            'background_updates_running': self.running
        }


# Global real-time manager instance
_real_time_manager: Optional[RealTimeDataManager] = None


def get_real_time_manager(socketio: SocketIO = None) -> Optional[RealTimeDataManager]:
    """Get the global real-time data manager instance"""
    global _real_time_manager
    if _real_time_manager is None and socketio:
        _real_time_manager = RealTimeDataManager(socketio)
    return _real_time_manager


def initialize_real_time_manager(socketio: SocketIO) -> RealTimeDataManager:
    """Initialize the real-time data manager"""
    global _real_time_manager
    _real_time_manager = RealTimeDataManager(socketio)
    _real_time_manager.start_background_updates()
    return _real_time_manager