"""
Real-Time Data Manager
Provides streaming market data and real-time updates
"""

import json
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
import yfinance as yf
import requests
from cache_manager import cache_manager
import schedule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeDataManager:
    def __init__(self, config_file: str = "config.json"):
        """Initialize real-time data manager"""
        self.config = self.load_config(config_file)
        self.is_running = False
        self.subscribers = {}
        self.data_queue = queue.Queue()
        self.last_prices = {}
        self.price_alerts = {}
        
        # Market hours (9:30 AM - 4:00 PM ET)
        self.market_open_hour = 9
        self.market_open_minute = 30
        self.market_close_hour = 16
        self.market_close_minute = 0
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'watchlist': ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL'],
                'update_interval': 60,  # seconds
                'price_change_threshold': 0.02  # 2%
            }
    
    def is_market_hours(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check time
        market_open = now.replace(hour=self.market_open_hour, minute=self.market_open_minute, second=0)
        market_close = now.replace(hour=self.market_close_hour, minute=self.market_close_minute, second=0)
        
        return market_open <= now <= market_close
    
    def get_real_time_quotes(self, symbols: List[str]) -> Dict:
        """Get real-time quotes for symbols"""
        try:
            quotes = {}
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get real-time data (1-minute interval, last 2 periods)
                    hist = ticker.history(period="1d", interval="1m")
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        
                        change = current_price - previous_price
                        change_pct = (change / previous_price) * 100 if previous_price != 0 else 0
                        
                        # Get additional real-time info
                        info = ticker.info
                        
                        quotes[symbol] = {
                            'symbol': symbol,
                            'price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_pct': round(change_pct, 2),
                            'volume': int(hist['Volume'].iloc[-1]),
                            'timestamp': datetime.now().isoformat(),
                            'market_cap': info.get('marketCap', 0),
                            'pe_ratio': info.get('trailingPE', 0),
                            'day_high': round(hist['High'].max(), 2),
                            'day_low': round(hist['Low'].min(), 2),
                            'avg_volume': int(hist['Volume'].mean())
                        }
                        
                        # Cache the data
                        cache_manager.cache_data('realtime', symbol, quotes[symbol])
                        
                except Exception as e:
                    logger.warning(f"Error getting real-time data for {symbol}: {e}")
                    
                    # Try to get cached data
                    cached_data = cache_manager.get_cached_data('realtime', symbol)
                    if cached_data:
                        quotes[symbol] = cached_data['data']
                    
                time.sleep(0.1)  # Rate limiting
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting real-time quotes: {e}")
            return {}
    
    def start_streaming(self, symbols: List[str], callback: Callable = None):
        """Start streaming real-time data"""
        self.is_running = True
        self.watchlist = symbols
        
        def stream_worker():
            logger.info(f"Starting real-time streaming for {len(symbols)} symbols")
            
            while self.is_running:
                try:
                    # Only stream during market hours or if forced
                    if self.is_market_hours() or not self.config.get('market_hours_only', True):
                        quotes = self.get_real_time_quotes(symbols)
                        
                        for symbol, quote in quotes.items():
                            # Check for significant price changes
                            self.check_price_alerts(symbol, quote)
                            
                            # Store latest price
                            self.last_prices[symbol] = quote
                            
                            # Call callback if provided
                            if callback:
                                callback(symbol, quote)
                            
                            # Put in queue for subscribers
                            self.data_queue.put({
                                'type': 'price_update',
                                'symbol': symbol,
                                'data': quote
                            })
                    
                    # Wait for next update
                    update_interval = self.config.get('update_interval', 60)
                    time.sleep(update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in streaming worker: {e}")
                    time.sleep(10)  # Wait before retry
        
        # Start streaming thread
        self.streaming_thread = threading.Thread(target=stream_worker, daemon=True)
        self.streaming_thread.start()
        
        logger.info("Real-time streaming started")
    
    def stop_streaming(self):
        """Stop streaming real-time data"""
        self.is_running = False
        logger.info("Real-time streaming stopped")
    
    def subscribe_to_updates(self, callback: Callable):
        """Subscribe to real-time updates"""
        subscriber_id = str(id(callback))
        self.subscribers[subscriber_id] = callback
        
        # Start queue processor if not running
        if not hasattr(self, 'queue_processor') or not self.queue_processor.is_alive():
            self.start_queue_processor()
        
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from updates"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
    
    def start_queue_processor(self):
        """Start processing queue for subscribers"""
        def process_queue():
            while self.is_running:
                try:
                    if not self.data_queue.empty():
                        update = self.data_queue.get(timeout=1)
                        
                        # Notify all subscribers
                        for subscriber_id, callback in self.subscribers.items():
                            try:
                                callback(update)
                            except Exception as e:
                                logger.warning(f"Error notifying subscriber {subscriber_id}: {e}")
                                
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing queue: {e}")
        
        self.queue_processor = threading.Thread(target=process_queue, daemon=True)
        self.queue_processor.start()
    
    def set_price_alert(self, symbol: str, price: float, alert_type: str = "above"):
        """Set price alert for symbol"""
        if symbol not in self.price_alerts:
            self.price_alerts[symbol] = []
        
        alert = {
            'price': price,
            'type': alert_type,  # 'above', 'below', 'change_pct'
            'created_at': datetime.now().isoformat(),
            'triggered': False
        }
        
        self.price_alerts[symbol].append(alert)
        logger.info(f"Price alert set for {symbol}: {alert_type} {price}")
    
    def check_price_alerts(self, symbol: str, quote: Dict):
        """Check if any price alerts should be triggered"""
        if symbol not in self.price_alerts:
            return
        
        current_price = quote['price']
        change_pct = abs(quote['change_pct'])
        
        for alert in self.price_alerts[symbol]:
            if alert['triggered']:
                continue
            
            triggered = False
            
            if alert['type'] == 'above' and current_price >= alert['price']:
                triggered = True
                message = f"{symbol} price {current_price} is above alert level {alert['price']}"
            elif alert['type'] == 'below' and current_price <= alert['price']:
                triggered = True
                message = f"{symbol} price {current_price} is below alert level {alert['price']}"
            elif alert['type'] == 'change_pct' and change_pct >= alert['price']:
                triggered = True
                message = f"{symbol} price change {change_pct:.1f}% exceeds alert threshold {alert['price']}%"
            
            if triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                
                # Send alert to queue
                self.data_queue.put({
                    'type': 'price_alert',
                    'symbol': symbol,
                    'message': message,
                    'alert': alert,
                    'quote': quote
                })
                
                logger.warning(f"PRICE ALERT: {message}")
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        return {
            'is_open': self.is_market_hours(),
            'next_open': self.get_next_market_open(),
            'next_close': self.get_next_market_close(),
            'current_time': datetime.now().isoformat()
        }
    
    def get_next_market_open(self) -> str:
        """Get next market open time"""
        now = datetime.now()
        
        # If it's weekend, next open is Monday
        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_open = now + timedelta(days=days_until_monday)
            return next_open.replace(hour=self.market_open_hour, minute=self.market_open_minute, second=0).isoformat()
        
        # If before market open today
        market_open_today = now.replace(hour=self.market_open_hour, minute=self.market_open_minute, second=0)
        if now < market_open_today:
            return market_open_today.isoformat()
        
        # Otherwise, next business day
        next_day = now + timedelta(days=1)
        if next_day.weekday() >= 5:  # If next day is weekend
            days_until_monday = 7 - next_day.weekday()
            next_day = next_day + timedelta(days=days_until_monday)
        
        return next_day.replace(hour=self.market_open_hour, minute=self.market_open_minute, second=0).isoformat()
    
    def get_next_market_close(self) -> str:
        """Get next market close time"""
        now = datetime.now()
        
        # If market is open today
        if self.is_market_hours():
            return now.replace(hour=self.market_close_hour, minute=self.market_close_minute, second=0).isoformat()
        
        # Otherwise, next business day close
        return self.get_next_market_open().replace('09:30:00', '16:00:00')
    
    def get_latest_quotes(self, symbols: List[str] = None) -> Dict:
        """Get latest cached quotes"""
        if symbols is None:
            symbols = list(self.last_prices.keys())
        
        return {symbol: self.last_prices.get(symbol, {}) for symbol in symbols}
    
    def force_update(self, symbols: List[str] = None) -> Dict:
        """Force immediate update of quotes"""
        if symbols is None:
            symbols = self.config.get('watchlist', [])
        
        return self.get_real_time_quotes(symbols)

# Global instance
real_time_manager = RealTimeDataManager()

def start_real_time_monitoring():
    """Start real-time monitoring with default configuration"""
    symbols = ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AAPL']
    
    def price_update_callback(symbol, quote):
        """Handle price updates"""
        change_pct = abs(quote.get('change_pct', 0))
        
        # Log significant moves
        if change_pct >= 2.0:
            logger.info(f"SIGNIFICANT MOVE: {symbol} {quote['change_pct']:+.1f}% to ${quote['price']}")
    
    # Set up price alerts
    real_time_manager.set_price_alert('NVDA', 180.0, 'above')
    real_time_manager.set_price_alert('TSLA', 300.0, 'below')
    real_time_manager.set_price_alert('NVDA', 3.0, 'change_pct')  # 3% change alert
    
    # Start streaming
    real_time_manager.start_streaming(symbols, price_update_callback)
    
    return real_time_manager

if __name__ == "__main__":
    print("Starting Real-Time Market Data Monitoring...")
    
    # Start monitoring
    rtm = start_real_time_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            
            # Print market status every minute
            status = rtm.get_market_status()
            latest_quotes = rtm.get_latest_quotes()
            
            print(f"\nMarket Status: {'OPEN' if status['is_open'] else 'CLOSED'}")
            print(f"Active Quotes: {len(latest_quotes)} symbols")
            
            # Show top movers
            if latest_quotes:
                sorted_quotes = sorted(
                    [(symbol, quote) for symbol, quote in latest_quotes.items() if quote],
                    key=lambda x: abs(x[1].get('change_pct', 0)),
                    reverse=True
                )
                
                print("Top Movers:")
                for symbol, quote in sorted_quotes[:3]:
                    print(f"  {symbol}: ${quote.get('price', 0):.2f} ({quote.get('change_pct', 0):+.1f}%)")
            
    except KeyboardInterrupt:
        print("\nStopping real-time monitoring...")
        rtm.stop_streaming()