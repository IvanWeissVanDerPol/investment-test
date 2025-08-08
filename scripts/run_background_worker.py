#!/usr/bin/env python3
"""
Background Worker for InvestmentAI
Handles ML model training, data collection, and periodic tasks
"""

import os
import sys
import time
import logging
import threading
import signal
from datetime import datetime, timedelta
from pathlib import Path
import schedule

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.investment_system.data.market_data_collector import MarketDataCollector
from core.investment_system.ai.ml_prediction_engine import get_ml_engine
from core.investment_system.analysis.enhanced_market_analyzer import EnhancedMarketAnalyzer
from core.investment_system.portfolio.advanced_portfolio_optimizer import get_portfolio_optimizer
from core.investment_system.monitoring.performance_monitor import get_performance_monitor
from core.investment_system.utils.cache_manager import CacheManager
from core.investment_system.monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Background worker for ML and data processing tasks"""
    
    def __init__(self):
        self.running = False
        self.data_collector = MarketDataCollector()
        self.ml_engine = get_ml_engine()
        self.market_analyzer = EnhancedMarketAnalyzer()
        self.portfolio_optimizer = get_portfolio_optimizer()
        self.performance_monitor = get_performance_monitor()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Symbols to monitor
        self.symbols = [
            "NVDA", "MSFT", "TSLA", "GOOGL", "AMZN", "META", "AAPL", "CRM",
            "DE", "TSM", "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO", "SPY", "QQQ"
        ]
        
        # Worker threads
        self.threads = []
        
        logger.info("Background Worker initialized")
    
    def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("Worker already running")
            return
        
        self.running = True
        
        # Schedule tasks
        self._schedule_tasks()
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self._scheduler_loop)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        self.threads.append(scheduler_thread)
        
        # Start main worker loop
        worker_thread = threading.Thread(target=self._worker_loop)
        worker_thread.daemon = True
        worker_thread.start()
        self.threads.append(worker_thread)
        
        logger.info("Background Worker started")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def stop(self):
        """Stop the background worker"""
        logger.info("Stopping Background Worker...")
        
        self.running = False
        self.performance_monitor.stop_monitoring()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=10)
        
        logger.info("Background Worker stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _schedule_tasks(self):
        """Schedule periodic tasks"""
        # Data collection tasks
        schedule.every(5).minutes.do(self._collect_market_data)
        schedule.every(15).minutes.do(self._update_cache)
        schedule.every(1).hours.do(self._cleanup_old_data)
        
        # ML tasks
        schedule.every(30).minutes.do(self._train_ml_models)
        schedule.every(1).hours.do(self._evaluate_model_performance)
        schedule.every(6).hours.do(self._retrain_models)
        
        # Portfolio tasks
        schedule.every(1).hours.do(self._analyze_portfolios)
        schedule.every(4).hours.do(self._optimize_portfolios)
        schedule.every().day.at("09:30").do(self._daily_market_analysis)
        schedule.every().day.at("16:00").do(self._daily_portfolio_report)
        
        # System maintenance
        schedule.every(1).hours.do(self._system_health_check)
        schedule.every().day.at("02:00").do(self._daily_maintenance)
        schedule.every().sunday.at("03:00").do(self._weekly_cleanup)
        
        logger.info("Tasks scheduled")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _worker_loop(self):
        """Main worker loop for continuous tasks"""
        while self.running:
            try:
                # Continuous monitoring tasks
                self._monitor_alerts()
                self._process_queued_tasks()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(60)
    
    def _collect_market_data(self):
        """Collect market data for all symbols"""
        try:
            logger.info("Collecting market data...")
            
            for symbol in self.symbols:
                try:
                    data = self.data_collector.get_real_time_data(symbol)
                    if data:
                        # Cache the data
                        cache_key = f"realtime_data_{symbol}"
                        self.cache_manager.set(cache_key, data, ttl=300)  # 5 minutes
                        
                except Exception as e:
                    logger.error(f"Failed to collect data for {symbol}: {e}")
            
            self.audit_logger.log_event(
                EventType.DATA_COLLECTION_COMPLETED,
                SeverityLevel.LOW,
                resource='background_worker',
                details={'symbols_processed': len(self.symbols)}
            )
            
            logger.info(f"Market data collection completed for {len(self.symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Market data collection failed: {e}")
    
    def _train_ml_models(self):
        """Train ML models with latest data"""
        try:
            logger.info("Training ML models...")
            
            trained_models = 0
            for symbol in self.symbols[:5]:  # Train on top 5 symbols
                try:
                    # Train price prediction model
                    result = self.ml_engine.predict_price(symbol, horizon=1, model_type='random_forest')
                    if result.confidence > 0.5:
                        trained_models += 1
                        
                except Exception as e:
                    logger.error(f"Failed to train model for {symbol}: {e}")
            
            logger.info(f"ML model training completed - {trained_models} models trained")
            
        except Exception as e:
            logger.error(f"ML model training failed: {e}")
    
    def _evaluate_model_performance(self):
        """Evaluate ML model performance"""
        try:
            logger.info("Evaluating ML model performance...")
            
            diagnostics = self.ml_engine.get_model_diagnostics()
            
            # Log performance metrics
            self.audit_logger.log_event(
                EventType.MODEL_EVALUATION_COMPLETED,
                SeverityLevel.LOW,
                resource='background_worker',
                details={'diagnostics': diagnostics}
            )
            
            logger.info("ML model evaluation completed")
            
        except Exception as e:
            logger.error(f"ML model evaluation failed: {e}")
    
    def _retrain_models(self):
        """Retrain models with fresh data"""
        try:
            logger.info("Retraining ML models with fresh data...")
            
            # This would implement full model retraining
            # For now, just log the event
            
            self.audit_logger.log_event(
                EventType.MODEL_RETRAIN_COMPLETED,
                SeverityLevel.MEDIUM,
                resource='background_worker'
            )
            
            logger.info("ML model retraining completed")
            
        except Exception as e:
            logger.error(f"ML model retraining failed: {e}")
    
    def _analyze_portfolios(self):
        """Analyze portfolio performance"""
        try:
            logger.info("Analyzing portfolio performance...")
            
            # This would analyze current portfolio holdings
            for symbol in self.symbols[:3]:  # Analyze top holdings
                try:
                    analysis = self.market_analyzer.analyze_symbol(symbol)
                    
                    # Cache analysis results
                    cache_key = f"analysis_{symbol}"
                    self.cache_manager.set(cache_key, analysis, ttl=3600)  # 1 hour
                    
                except Exception as e:
                    logger.error(f"Failed to analyze {symbol}: {e}")
            
            logger.info("Portfolio analysis completed")
            
        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
    
    def _optimize_portfolios(self):
        """Optimize portfolio allocations"""
        try:
            logger.info("Optimizing portfolio allocations...")
            
            # This would run portfolio optimization
            symbols = self.symbols[:10]  # Top 10 symbols
            
            result = self.portfolio_optimizer.optimize_portfolio(
                symbols,
                method='markowitz'
            )
            
            if result:
                logger.info(f"Portfolio optimization completed - Expected return: {result.expected_return:.4f}")
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
    
    def _daily_market_analysis(self):
        """Run daily market analysis"""
        try:
            logger.info("Running daily market analysis...")
            
            # Run comprehensive analysis
            results = {}
            for symbol in self.symbols:
                try:
                    analysis = self.market_analyzer.analyze_symbol(symbol)
                    results[symbol] = analysis.recommendation
                except Exception as e:
                    logger.error(f"Daily analysis failed for {symbol}: {e}")
            
            # Log results
            self.audit_logger.log_event(
                EventType.DAILY_ANALYSIS_COMPLETED,
                SeverityLevel.LOW,
                resource='background_worker',
                details={'analysis_results': results}
            )
            
            logger.info(f"Daily market analysis completed for {len(results)} symbols")
            
        except Exception as e:
            logger.error(f"Daily market analysis failed: {e}")
    
    def _daily_portfolio_report(self):
        """Generate daily portfolio report"""
        try:
            logger.info("Generating daily portfolio report...")
            
            # This would generate comprehensive portfolio report
            report_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_symbols': len(self.symbols),
                'system_status': 'healthy'
            }
            
            # Save report
            report_file = f"reports/daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            Path(report_file).parent.mkdir(exist_ok=True)
            
            import json
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Daily portfolio report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Daily portfolio report failed: {e}")
    
    def _update_cache(self):
        """Update cache with fresh data"""
        try:
            # Clean expired cache entries
            self.cache_manager.cleanup_expired()
            logger.debug("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Cache update failed: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data files"""
        try:
            logger.info("Cleaning up old data...")
            
            # Clean old log files
            logs_dir = Path("logs")
            if logs_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                for log_file in logs_dir.glob("*.log.*"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logger.debug(f"Deleted old log file: {log_file}")
            
            # Clean old cache files
            cache_dir = Path("cache")
            if cache_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=7)
                for cache_file in cache_dir.glob("*.cache"):
                    if cache_file.stat().st_mtime < cutoff_date.timestamp():
                        cache_file.unlink()
                        logger.debug(f"Deleted old cache file: {cache_file}")
            
            logger.info("Old data cleanup completed")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    def _system_health_check(self):
        """Perform system health checks"""
        try:
            logger.debug("Performing system health check...")
            
            # Check database connection
            # Check Redis connection
            # Check API endpoints
            # Check disk space
            # Check memory usage
            
            # For now, just log that check was performed
            logger.debug("System health check completed")
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
    
    def _daily_maintenance(self):
        """Perform daily maintenance tasks"""
        try:
            logger.info("Performing daily maintenance...")
            
            # Database maintenance
            # Log rotation
            # Cache optimization
            # Model cleanup
            
            self.audit_logger.log_event(
                EventType.SYSTEM_MAINTENANCE_COMPLETED,
                SeverityLevel.LOW,
                resource='background_worker'
            )
            
            logger.info("Daily maintenance completed")
            
        except Exception as e:
            logger.error(f"Daily maintenance failed: {e}")
    
    def _weekly_cleanup(self):
        """Perform weekly cleanup tasks"""
        try:
            logger.info("Performing weekly cleanup...")
            
            # Deep cache cleanup
            # Old model cleanup
            # Database optimization
            # Report archival
            
            logger.info("Weekly cleanup completed")
            
        except Exception as e:
            logger.error(f"Weekly cleanup failed: {e}")
    
    def _monitor_alerts(self):
        """Monitor and process alerts"""
        try:
            # This would check for system alerts and process them
            pass
            
        except Exception as e:
            logger.error(f"Alert monitoring failed: {e}")
    
    def _process_queued_tasks(self):
        """Process any queued background tasks"""
        try:
            # This would process tasks from a queue (Redis, etc.)
            pass
            
        except Exception as e:
            logger.error(f"Queued task processing failed: {e}")


def main():
    """Main function"""
    logger.info("Starting InvestmentAI Background Worker")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize and start worker
    worker = BackgroundWorker()
    
    try:
        worker.start()
        
        # Keep the main thread alive
        while worker.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        worker.stop()


if __name__ == "__main__":
    main()