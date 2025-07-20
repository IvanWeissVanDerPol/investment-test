#!/usr/bin/env python3
"""
Investment Analysis System Monitor
Continuous monitoring and alerting for the investment analysis system
"""

import json
import time
import schedule
import logging
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../reports/system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InvestmentSystemMonitor:
    """Monitor investment analysis system health and market conditions"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.last_check = datetime.now()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_file} not found")
            return {}
    
    def check_system_health(self) -> Dict[str, bool]:
        """Check overall system health"""
        health_status = {
            'config_valid': self.validate_config(),
            'api_accessible': self.check_api_connectivity(),
            'cache_healthy': self.check_cache_status(),
            'reports_generating': self.check_recent_reports(),
            'disk_space_ok': self.check_disk_space()
        }
        
        logger.info(f"System health check: {health_status}")
        return health_status
    
    def validate_config(self) -> bool:
        """Validate configuration file"""
        try:
            required_fields = ['user_profile', 'target_stocks', 'ai_robotics_etfs']
            return all(field in self.config for field in required_fields)
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False
    
    def check_api_connectivity(self) -> bool:
        """Check API endpoints"""
        test_urls = [
            "https://query1.finance.yahoo.com/v1/finance/search?q=NVDA",
            "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
        ]
        
        for url in test_urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code >= 400:
                    logger.warning(f"API endpoint issue: {url} returned {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"API connectivity failed for {url}: {e}")
                return False
        
        return True
    
    def check_cache_status(self) -> bool:
        """Check cache health"""
        try:
            cache_dir = Path("../cache")
            if not cache_dir.exists():
                return True  # No cache is OK
            
            cache_files = list(cache_dir.glob("*.json"))
            fresh_count = 0
            
            for cache_file in cache_files:
                age_hours = (datetime.now() - datetime.fromtimestamp(
                    cache_file.stat().st_mtime)).total_seconds() / 3600
                if age_hours < 24:
                    fresh_count += 1
            
            # At least 50% of cache should be fresh
            if cache_files and fresh_count / len(cache_files) < 0.5:
                logger.warning("Cache mostly stale")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return False
    
    def check_recent_reports(self) -> bool:
        """Check if reports are being generated"""
        try:
            reports_dir = Path("../reports")
            if not reports_dir.exists():
                return False
            
            cutoff = datetime.now() - timedelta(hours=24)
            recent_reports = [
                f for f in reports_dir.glob("*.json")
                if datetime.fromtimestamp(f.stat().st_mtime) > cutoff
            ]
            
            return len(recent_reports) > 0
            
        except Exception as e:
            logger.error(f"Reports check failed: {e}")
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(Path.cwd())
            free_gb = free / (1024**3)
            
            # Warn if less than 1GB free
            if free_gb < 1.0:
                logger.warning(f"Low disk space: {free_gb:.2f} GB remaining")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return False
    
    def monitor_price_movements(self) -> List[Dict]:
        """Monitor for significant price movements"""
        alerts = []
        
        try:
            target_stocks = self.config.get('target_stocks', [])[:10]  # Monitor top 10
            threshold = self.config.get('alert_thresholds', {}).get('price_movement_alert', 0.05)
            
            for symbol in target_stocks:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'][-1]
                        prev_price = hist['Close'][-2]
                        change_pct = ((current_price / prev_price) - 1) * 100
                        
                        if abs(change_pct) >= (threshold * 100):
                            alerts.append({
                                'symbol': symbol,
                                'change_pct': change_pct,
                                'current_price': current_price,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                except Exception as e:
                    logger.warning(f"Failed to check {symbol}: {e}")
            
        except Exception as e:
            logger.error(f"Price monitoring failed: {e}")
        
        if alerts:
            logger.info(f"Price alerts: {alerts}")
        
        return alerts
    
    def check_trading_hours(self) -> bool:
        """Check if markets are open"""
        now = datetime.now()
        
        # Simple check: weekdays 9:30 AM - 4:00 PM ET
        # Note: This is simplified and doesn't account for holidays
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Rough market hours check (would need timezone handling for production)
        hour = now.hour
        return 9 <= hour <= 16
    
    def send_alert(self, subject: str, message: str) -> bool:
        """Send email alert"""
        try:
            email_settings = self.config.get('email_settings', {})
            
            if not email_settings.get('enabled', False):
                logger.info("Email alerts disabled")
                return True
            
            msg = MimeMultipart()
            msg['From'] = email_settings['username']
            msg['To'] = email_settings['recipient']
            msg['Subject'] = f"Investment System Alert: {subject}"
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
            server.starttls()
            server.login(email_settings['username'], email_settings['password'])
            server.sendmail(email_settings['username'], email_settings['recipient'], msg.as_string())
            server.quit()
            
            logger.info(f"Alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def run_monitoring_cycle(self):
        """Run complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        # Check system health
        health = self.check_system_health()
        unhealthy_systems = [k for k, v in health.items() if not v]
        
        if unhealthy_systems:
            alert_msg = f"System health issues detected:\n" + "\n".join(
                f"- {system}" for system in unhealthy_systems
            )
            self.send_alert("System Health Warning", alert_msg)
        
        # Monitor prices during trading hours
        if self.check_trading_hours():
            price_alerts = self.monitor_price_movements()
            
            if price_alerts:
                alert_msg = "Price Movement Alerts:\n\n"
                for alert in price_alerts:
                    alert_msg += f"{alert['symbol']}: {alert['change_pct']:+.2f}% (${alert['current_price']:.2f})\n"
                
                self.send_alert("Price Movement Alert", alert_msg)
        
        # Log monitoring completion
        self.last_check = datetime.now()
        logger.info(f"Monitoring cycle completed at {self.last_check}")
    
    def start_scheduled_monitoring(self, interval_minutes: int = 15):
        """Start scheduled monitoring"""
        logger.info(f"Starting scheduled monitoring (every {interval_minutes} minutes)")
        
        # Schedule monitoring
        schedule.every(interval_minutes).minutes.do(self.run_monitoring_cycle)
        
        # Schedule daily health report
        schedule.every().day.at("08:00").do(self.daily_health_report)
        
        # Run initial check
        self.run_monitoring_cycle()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def daily_health_report(self):
        """Generate daily health report"""
        logger.info("Generating daily health report...")
        
        health = self.check_system_health()
        
        report = f"""
Daily Investment System Health Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

System Status:
- Configuration: {'✅' if health['config_valid'] else '❌'}
- API Connectivity: {'✅' if health['api_accessible'] else '❌'}
- Cache Health: {'✅' if health['cache_healthy'] else '❌'}
- Report Generation: {'✅' if health['reports_generating'] else '❌'}
- Disk Space: {'✅' if health['disk_space_ok'] else '❌'}

Portfolio Status:
- Balance: ${self.config.get('user_profile', {}).get('dukascopy_balance', 0)}
- Risk Tolerance: {self.config.get('user_profile', {}).get('risk_tolerance', 'Unknown')}

Monitoring Status: Active
Last Check: {self.last_check.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_alert("Daily Health Report", report)


def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Investment System Monitor')
    parser.add_argument('--interval', type=int, default=15, 
                       help='Monitoring interval in minutes (default: 15)')
    parser.add_argument('--one-shot', action='store_true',
                       help='Run monitoring once and exit')
    
    args = parser.parse_args()
    
    monitor = InvestmentSystemMonitor()
    
    if args.one_shot:
        monitor.run_monitoring_cycle()
    else:
        monitor.start_scheduled_monitoring(args.interval)


if __name__ == "__main__":
    main()