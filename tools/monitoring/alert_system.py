"""
Real-Time Alert and Monitoring System
Automated alerts for price movements, news events, and trading signals
"""

import json
import time
import threading
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
import schedule
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import yfinance as yf
from real_time_data_manager import real_time_manager
from cache_manager import cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self, config_file: str = "config.json"):
        """Initialize alert system"""
        self.config = self.load_config(config_file)
        self.active_alerts = {}
        self.triggered_alerts = []
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Alert types
        self.alert_types = {
            'price_above': 'Price Above Threshold',
            'price_below': 'Price Below Threshold',
            'price_change': 'Price Change Percentage',
            'volume_spike': 'Volume Spike',
            'technical_signal': 'Technical Analysis Signal',
            'news_alert': 'Major News Event',
            'earnings_reminder': 'Earnings Date Reminder',
            'volatility_spike': 'Volatility Spike'
        }
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'email': {
                    'enabled': False,  # Disabled by default
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'recipient': ''
                },
                'monitoring_interval': 300,  # 5 minutes
                'alert_cooldown': 3600,  # 1 hour between same alerts
                'watchlist': ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL']
            }
    
    def create_alert(self, alert_type: str, symbol: str, threshold: float, 
                    condition: str = 'above', message: str = None) -> str:
        """Create a new alert"""
        try:
            alert_id = f"{symbol}_{alert_type}_{int(time.time())}"
            
            alert = {
                'id': alert_id,
                'type': alert_type,
                'symbol': symbol,
                'threshold': threshold,
                'condition': condition,
                'message': message or f"{symbol} {alert_type} alert",
                'created_at': datetime.now().isoformat(),
                'triggered': False,
                'last_triggered': None,
                'trigger_count': 0
            }
            
            self.active_alerts[alert_id] = alert
            logger.info(f"Alert created: {alert_id}")
            
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert"""
        try:
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                logger.info(f"Alert removed: {alert_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing alert: {e}")
            return False
    
    def check_price_alerts(self, symbol: str, current_price: float, price_change_pct: float):
        """Check price-based alerts"""
        try:
            for alert_id, alert in self.active_alerts.items():
                if alert['symbol'] != symbol or alert['triggered']:
                    continue
                
                triggered = False
                
                # Price threshold alerts
                if alert['type'] == 'price_above' and current_price >= alert['threshold']:
                    triggered = True
                elif alert['type'] == 'price_below' and current_price <= alert['threshold']:
                    triggered = True
                elif alert['type'] == 'price_change' and abs(price_change_pct) >= alert['threshold']:
                    triggered = True
                
                if triggered:
                    self.trigger_alert(alert_id, {
                        'current_price': current_price,
                        'price_change_pct': price_change_pct,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
    
    def check_volume_alerts(self, symbol: str, current_volume: int, avg_volume: int):
        """Check volume-based alerts"""
        try:
            if avg_volume == 0:
                return
                
            volume_ratio = current_volume / avg_volume
            
            for alert_id, alert in self.active_alerts.items():
                if (alert['symbol'] == symbol and 
                    alert['type'] == 'volume_spike' and 
                    not alert['triggered'] and
                    volume_ratio >= alert['threshold']):
                    
                    self.trigger_alert(alert_id, {
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error checking volume alerts: {e}")
    
    def check_technical_alerts(self, symbol: str, technical_analysis: Dict):
        """Check technical analysis alerts"""
        try:
            for alert_id, alert in self.active_alerts.items():
                if (alert['symbol'] == symbol and 
                    alert['type'] == 'technical_signal' and 
                    not alert['triggered']):
                    
                    # Check for specific signals
                    signals = technical_analysis.get('signals', [])
                    recommendation = technical_analysis.get('recommendation', '')
                    
                    # Trigger on strong buy/sell signals
                    if (alert['condition'] == 'strong_buy' and recommendation == 'STRONG BUY') or \
                       (alert['condition'] == 'buy' and recommendation in ['BUY', 'STRONG BUY']) or \
                       (alert['condition'] == 'sell' and 'sell' in recommendation.lower()):
                        
                        self.trigger_alert(alert_id, {
                            'recommendation': recommendation,
                            'signals': signals,
                            'confidence': technical_analysis.get('confidence', 0),
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            logger.error(f"Error checking technical alerts: {e}")
    
    def trigger_alert(self, alert_id: str, trigger_data: Dict):
        """Trigger an alert"""
        try:
            if alert_id not in self.active_alerts:
                return
            
            alert = self.active_alerts[alert_id]
            
            # Check cooldown period
            if alert['last_triggered']:
                last_trigger_time = datetime.fromisoformat(alert['last_triggered'])
                cooldown_seconds = self.config.get('alert_cooldown', 3600)
                
                if (datetime.now() - last_trigger_time).total_seconds() < cooldown_seconds:
                    logger.debug(f"Alert {alert_id} in cooldown period")
                    return
            
            # Update alert status
            alert['triggered'] = True
            alert['last_triggered'] = datetime.now().isoformat()
            alert['trigger_count'] += 1
            
            # Create alert message
            alert_message = self.format_alert_message(alert, trigger_data)
            
            # Store triggered alert
            triggered_alert = {
                'alert': alert.copy(),
                'trigger_data': trigger_data,
                'message': alert_message,
                'timestamp': datetime.now().isoformat()
            }
            
            self.triggered_alerts.append(triggered_alert)
            
            # Send notifications
            self.send_notifications(alert_message, alert)
            
            logger.warning(f"ALERT TRIGGERED: {alert_message}")
            
            # Reset triggered status after cooldown
            def reset_alert():
                time.sleep(self.config.get('alert_cooldown', 3600))
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id]['triggered'] = False
            
            threading.Thread(target=reset_alert, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    def format_alert_message(self, alert: Dict, trigger_data: Dict) -> str:
        """Format alert message"""
        try:
            symbol = alert['symbol']
            alert_type = self.alert_types.get(alert['type'], alert['type'])
            
            if alert['type'] in ['price_above', 'price_below']:
                current_price = trigger_data.get('current_price', 0)
                threshold = alert['threshold']
                return f"{alert_type}: {symbol} price ${current_price:.2f} crossed threshold ${threshold:.2f}"
            
            elif alert['type'] == 'price_change':
                change_pct = trigger_data.get('price_change_pct', 0)
                threshold = alert['threshold']
                return f"{alert_type}: {symbol} moved {change_pct:+.1f}% (threshold: {threshold:.1f}%)"
            
            elif alert['type'] == 'volume_spike':
                volume_ratio = trigger_data.get('volume_ratio', 0)
                threshold = alert['threshold']
                return f"{alert_type}: {symbol} volume {volume_ratio:.1f}x above average (threshold: {threshold:.1f}x)"
            
            elif alert['type'] == 'technical_signal':
                recommendation = trigger_data.get('recommendation', '')
                confidence = trigger_data.get('confidence', 0)
                return f"{alert_type}: {symbol} technical analysis shows {recommendation} (confidence: {confidence:.1%})"
            
            else:
                return f"{alert_type}: {symbol} - {alert.get('message', 'Alert triggered')}"
                
        except Exception as e:
            logger.error(f"Error formatting alert message: {e}")
            return f"Alert triggered for {alert.get('symbol', 'Unknown')}"
    
    def send_notifications(self, message: str, alert: Dict):
        """Send alert notifications"""
        try:
            # Console notification (always enabled)
            print(f"\n🚨 INVESTMENT ALERT: {message}")
            
            # Email notification (if configured)
            if self.config.get('email', {}).get('enabled', False):
                self.send_email_alert(message, alert)
            
            # File notification
            self.log_alert_to_file(message, alert)
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def send_email_alert(self, message: str, alert: Dict):
        """Send email alert"""
        try:
            email_config = self.config.get('email', {})
            
            if not all([email_config.get('username'), email_config.get('password'), email_config.get('recipient')]):
                logger.warning("Email configuration incomplete")
                return
            
            # Create email
            msg = MimeMultipart()
            msg['From'] = email_config['username']
            msg['To'] = email_config['recipient']
            msg['Subject'] = f"Investment Alert: {alert['symbol']}"
            
            # Email body
            body = f"""
Investment Alert Triggered

Symbol: {alert['symbol']}
Alert Type: {self.alert_types.get(alert['type'], alert['type'])}
Message: {message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your investment monitoring system.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def log_alert_to_file(self, message: str, alert: Dict):
        """Log alert to file"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'symbol': alert['symbol'],
                'type': alert['type'],
                'message': message,
                'alert_id': alert['id']
            }
            
            # Append to alerts log file
            log_file = "C:\\Users\\jandr\\Documents\\ivan\\reports\\alerts_log.json"
            
            try:
                with open(log_file, 'r') as f:
                    alerts_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                alerts_log = []
            
            alerts_log.append(log_entry)
            
            # Keep only last 1000 alerts
            if len(alerts_log) > 1000:
                alerts_log = alerts_log[-1000:]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(alerts_log, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error logging alert to file: {e}")
    
    def start_monitoring(self, symbols: List[str] = None):
        """Start real-time monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already running")
            return
        
        if symbols is None:
            symbols = self.config.get('watchlist', [])
        
        self.is_monitoring = True
        
        def monitoring_worker():
            logger.info(f"Starting alert monitoring for {len(symbols)} symbols")
            
            while self.is_monitoring:
                try:
                    # Get current market data
                    quotes = real_time_manager.get_real_time_quotes(symbols)
                    
                    for symbol, quote in quotes.items():
                        if not quote:
                            continue
                        
                        # Check price alerts
                        self.check_price_alerts(
                            symbol,
                            quote.get('price', 0),
                            quote.get('change_pct', 0)
                        )
                        
                        # Check volume alerts
                        self.check_volume_alerts(
                            symbol,
                            quote.get('volume', 0),
                            quote.get('avg_volume', 1)
                        )
                    
                    # Wait for next check
                    time.sleep(self.config.get('monitoring_interval', 300))
                    
                except Exception as e:
                    logger.error(f"Error in monitoring worker: {e}")
                    time.sleep(60)  # Wait before retry
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Alert monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        logger.info("Alert monitoring stopped")
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alerts"""
        try:
            active_count = len(self.active_alerts)
            triggered_count = len(self.triggered_alerts)
            
            # Recent alerts (last 24 hours)
            recent_alerts = [
                alert for alert in self.triggered_alerts
                if datetime.fromisoformat(alert['timestamp']) > datetime.now() - timedelta(hours=24)
            ]
            
            return {
                'active_alerts': active_count,
                'triggered_alerts': triggered_count,
                'recent_alerts_24h': len(recent_alerts),
                'monitoring_status': 'Running' if self.is_monitoring else 'Stopped',
                'watchlist_size': len(self.config.get('watchlist', [])),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting alert summary: {e}")
            return {'error': str(e)}
    
    def setup_default_alerts(self, symbols: List[str]):
        """Setup default alerts for symbols"""
        try:
            logger.info(f"Setting up default alerts for {len(symbols)} symbols")
            
            for symbol in symbols:
                # Get current price for thresholds
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.history(period="1d")['Close'].iloc[-1]
                    
                    # Price movement alerts (±5%)
                    self.create_alert('price_change', symbol, 5.0, 'above', 
                                    f"{symbol} moved more than 5%")
                    
                    # Volume spike alert (2x average)
                    self.create_alert('volume_spike', symbol, 2.0, 'above',
                                    f"{symbol} volume spike detected")
                    
                    # Price threshold alerts (±10% from current)
                    self.create_alert('price_above', symbol, current_price * 1.10, 'above',
                                    f"{symbol} broke above 10% resistance")
                    self.create_alert('price_below', symbol, current_price * 0.90, 'below',
                                    f"{symbol} broke below 10% support")
                    
                except Exception as e:
                    logger.warning(f"Could not set up alerts for {symbol}: {e}")
            
            logger.info(f"Default alerts setup complete: {len(self.active_alerts)} alerts active")
            
        except Exception as e:
            logger.error(f"Error setting up default alerts: {e}")

def start_alert_monitoring():
    """Start the alert monitoring system"""
    print("Starting Investment Alert System...")
    
    # Initialize alert system
    alert_system = AlertSystem()
    
    # Setup default alerts
    symbols = ['NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AAPL']
    alert_system.setup_default_alerts(symbols)
    
    # Create some custom alerts
    alert_system.create_alert('price_above', 'NVDA', 180.0, 'above', 'NVDA hit $180')
    alert_system.create_alert('price_below', 'TSLA', 300.0, 'below', 'TSLA dropped below $300')
    
    # Start monitoring
    alert_system.start_monitoring(symbols)
    
    print(f"Alert system started with {len(alert_system.active_alerts)} active alerts")
    print("Monitoring every 5 minutes for price movements, volume spikes, and technical signals")
    
    return alert_system

if __name__ == "__main__":
    # Start alert system
    alert_sys = start_alert_monitoring()
    
    try:
        # Keep running and show periodic status
        while True:
            time.sleep(300)  # 5 minutes
            
            summary = alert_sys.get_alert_summary()
            print(f"\nAlert Summary: {summary['active_alerts']} active, "
                  f"{summary['recent_alerts_24h']} triggered today")
            
            # Show recent alerts
            if alert_sys.triggered_alerts:
                print("Recent Alerts:")
                for alert in alert_sys.triggered_alerts[-3:]:  # Last 3 alerts
                    print(f"  {alert['timestamp']}: {alert['message']}")
    
    except KeyboardInterrupt:
        print("\nStopping alert system...")
        alert_sys.stop_monitoring()