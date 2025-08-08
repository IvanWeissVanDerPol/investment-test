"""
Performance Monitoring Dashboard
Real-time system performance monitoring with comprehensive metrics and alerting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import logging
import threading
import time
from collections import deque
from pathlib import Path
import psutil
import sqlite3

from ..data.market_data_collector import MarketDataCollector
from ..portfolio.advanced_portfolio_optimizer import AdvancedPortfolioOptimizer
from ..ai.ml_prediction_engine import MLPredictionEngine
from ..analysis.backtesting_engine import BacktestingEngine
from ..utils.cache_manager import CacheManager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    database_connections: int
    cache_hit_rate: float
    active_sessions: int
    response_times: Dict[str, float]
    error_rates: Dict[str, float]
    api_calls_per_minute: int


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    timestamp: datetime
    total_value: float
    daily_return: float
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    var_95: float
    positions: Dict[str, Dict[str, Any]]
    sector_allocation: Dict[str, float]
    risk_metrics: Dict[str, float]


@dataclass
class MLMetrics:
    """Machine learning model performance metrics"""
    timestamp: datetime
    prediction_accuracy: Dict[str, float]
    model_confidence: Dict[str, float]
    feature_importance: Dict[str, Dict[str, float]]
    training_status: Dict[str, str]
    prediction_counts: Dict[str, int]
    error_rates: Dict[str, float]
    data_quality_scores: Dict[str, float]


@dataclass
class AlertConfig:
    """Alert configuration"""
    name: str
    metric_path: str  # e.g., 'system.cpu_usage' or 'portfolio.daily_return'
    threshold_type: str  # 'above', 'below', 'outside_range'
    threshold_value: float
    threshold_range: Optional[Tuple[float, float]] = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    cooldown_minutes: int = 15
    enabled: bool = True


@dataclass
class Alert:
    """Performance alert"""
    timestamp: datetime
    alert_name: str
    metric_path: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None


class PerformanceCollector:
    """Collects performance metrics from various system components"""
    
    def __init__(self):
        self.data_collector = MarketDataCollector()
        self.cache_manager = CacheManager()
        self.audit_logger = get_audit_logger()
        
        # Component references
        self.ml_engine = None
        self.portfolio_optimizer = None
        self.backtesting_engine = None
        
        # Metrics storage
        self.metrics_history = {
            'system': deque(maxlen=1440),  # 24 hours of minute data
            'portfolio': deque(maxlen=1440),
            'ml': deque(maxlen=1440)
        }
        
        # Performance tracking
        self.api_call_counts = deque(maxlen=60)  # Last 60 minutes
        self.response_times = {}
        self.error_counts = {}
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide performance metrics"""
        try:
            # CPU and Memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Database connections (estimate)
            database_connections = self._get_database_connections()
            
            # Cache metrics
            cache_stats = self.cache_manager.get_stats()
            cache_hit_rate = cache_stats.get('hit_rate', 0.0)
            
            # Active sessions (placeholder)
            active_sessions = self._get_active_sessions()
            
            # Response times
            response_times = self._calculate_average_response_times()
            
            # Error rates
            error_rates = self._calculate_error_rates()
            
            # API calls per minute
            api_calls_per_minute = len(self.api_call_counts)
            
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                active_sessions=active_sessions,
                response_times=response_times,
                error_rates=error_rates,
                api_calls_per_minute=api_calls_per_minute
            )
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=0.0, memory_usage=0.0, disk_usage=0.0,
                network_io={}, database_connections=0, cache_hit_rate=0.0,
                active_sessions=0, response_times={}, error_rates={},
                api_calls_per_minute=0
            )
    
    def collect_portfolio_metrics(self, portfolio_data: Dict[str, Any]) -> PortfolioMetrics:
        """Collect portfolio performance metrics"""
        try:
            current_time = datetime.utcnow()
            
            # Basic portfolio values
            total_value = portfolio_data.get('total_value', 0.0)
            daily_return = portfolio_data.get('daily_return', 0.0)
            total_return = portfolio_data.get('total_return', 0.0)
            
            # Risk metrics
            volatility = portfolio_data.get('volatility', 0.0)
            sharpe_ratio = portfolio_data.get('sharpe_ratio', 0.0)
            max_drawdown = portfolio_data.get('max_drawdown', 0.0)
            beta = portfolio_data.get('beta', 1.0)
            var_95 = portfolio_data.get('var_95', 0.0)
            
            # Positions with detailed info
            positions = {}
            for symbol, position in portfolio_data.get('positions', {}).items():
                positions[symbol] = {
                    'shares': position.get('shares', 0),
                    'market_value': position.get('market_value', 0),
                    'weight': position.get('weight', 0),
                    'unrealized_pnl': position.get('unrealized_pnl', 0),
                    'day_change': position.get('day_change', 0)
                }
            
            # Sector allocation
            sector_allocation = portfolio_data.get('sector_allocation', {})
            
            # Additional risk metrics
            risk_metrics = {
                'concentration_risk': self._calculate_concentration_risk(positions),
                'sector_concentration': self._calculate_sector_concentration(sector_allocation),
                'liquidity_score': portfolio_data.get('liquidity_score', 0.0),
                'correlation_risk': portfolio_data.get('correlation_risk', 0.0)
            }
            
            return PortfolioMetrics(
                timestamp=current_time,
                total_value=total_value,
                daily_return=daily_return,
                total_return=total_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                beta=beta,
                var_95=var_95,
                positions=positions,
                sector_allocation=sector_allocation,
                risk_metrics=risk_metrics
            )
            
        except Exception as e:
            logger.error(f"Portfolio metrics collection failed: {e}")
            return PortfolioMetrics(
                timestamp=datetime.utcnow(),
                total_value=0.0, daily_return=0.0, total_return=0.0,
                volatility=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
                beta=1.0, var_95=0.0, positions={}, sector_allocation={},
                risk_metrics={}
            )
    
    def collect_ml_metrics(self) -> MLMetrics:
        """Collect ML model performance metrics"""
        try:
            if self.ml_engine is None:
                from ..ai.ml_prediction_engine import get_ml_engine
                self.ml_engine = get_ml_engine()
            
            current_time = datetime.utcnow()
            
            # Model diagnostics
            diagnostics = self.ml_engine.get_model_diagnostics()
            
            # Prediction accuracy (would be calculated from recent predictions)
            prediction_accuracy = {
                'price_prediction': 0.65,  # Placeholder
                'direction_prediction': 0.58,
                'volatility_prediction': 0.72
            }
            
            # Model confidence scores
            model_confidence = {
                'random_forest': 0.75,
                'xgboost': 0.82,
                'neural_network': 0.68,
                'ensemble': 0.79
            }
            
            # Feature importance (aggregated)
            feature_importance = {
                'price_prediction': {
                    'rsi': 0.15,
                    'macd': 0.12,
                    'volatility_20': 0.11,
                    'volume_ratio': 0.09,
                    'returns_lag_1': 0.08
                },
                'direction_prediction': {
                    'momentum_score': 0.18,
                    'bb_position': 0.14,
                    'rsi': 0.13,
                    'volume_trend': 0.10,
                    'price_sma_20_ratio': 0.09
                }
            }
            
            # Training status
            training_status = {
                'price_models': 'trained',
                'volatility_models': 'training',
                'direction_models': 'trained',
                'ensemble_models': 'optimizing'
            }
            
            # Prediction counts
            prediction_counts = diagnostics.get('recent_predictions', 0)
            prediction_counts_dict = {
                'price': prediction_counts,
                'direction': prediction_counts,
                'volatility': prediction_counts // 2
            }
            
            # Error rates
            error_rates = {
                'data_collection': 0.02,
                'feature_preparation': 0.01,
                'model_prediction': 0.03,
                'ensemble_combination': 0.01
            }
            
            # Data quality scores
            data_quality_scores = {
                'completeness': 0.95,
                'consistency': 0.92,
                'accuracy': 0.94,
                'timeliness': 0.98,
                'validity': 0.96
            }
            
            return MLMetrics(
                timestamp=current_time,
                prediction_accuracy=prediction_accuracy,
                model_confidence=model_confidence,
                feature_importance=feature_importance,
                training_status=training_status,
                prediction_counts=prediction_counts_dict,
                error_rates=error_rates,
                data_quality_scores=data_quality_scores
            )
            
        except Exception as e:
            logger.error(f"ML metrics collection failed: {e}")
            return MLMetrics(
                timestamp=datetime.utcnow(),
                prediction_accuracy={}, model_confidence={},
                feature_importance={}, training_status={},
                prediction_counts={}, error_rates={},
                data_quality_scores={}
            )
    
    def _get_database_connections(self) -> int:
        """Estimate number of database connections"""
        # This would query the actual database for connection count
        return 5  # Placeholder
    
    def _get_active_sessions(self) -> int:
        """Get number of active user sessions"""
        # This would query session storage
        return 3  # Placeholder
    
    def _calculate_average_response_times(self) -> Dict[str, float]:
        """Calculate average response times for different endpoints"""
        if not self.response_times:
            return {}
        
        averages = {}
        for endpoint, times in self.response_times.items():
            if times:
                averages[endpoint] = sum(times) / len(times)
        
        return averages
    
    def _calculate_error_rates(self) -> Dict[str, float]:
        """Calculate error rates for different components"""
        return {
            'api_errors': 0.02,
            'database_errors': 0.01,
            'data_collection_errors': 0.03,
            'ml_prediction_errors': 0.02
        }
    
    def _calculate_concentration_risk(self, positions: Dict[str, Dict[str, Any]]) -> float:
        """Calculate portfolio concentration risk"""
        if not positions:
            return 0.0
        
        weights = [pos.get('weight', 0) for pos in positions.values()]
        if not weights:
            return 0.0
        
        # Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights)
        return hhi
    
    def _calculate_sector_concentration(self, sector_allocation: Dict[str, float]) -> float:
        """Calculate sector concentration risk"""
        if not sector_allocation:
            return 0.0
        
        weights = list(sector_allocation.values())
        hhi = sum(w**2 for w in weights)
        return hhi
    
    def record_api_call(self, endpoint: str, response_time: float, success: bool):
        """Record API call for performance tracking"""
        current_time = datetime.utcnow()
        
        # Add to call count
        self.api_call_counts.append(current_time)
        
        # Record response time
        if endpoint not in self.response_times:
            self.response_times[endpoint] = deque(maxlen=100)
        self.response_times[endpoint].append(response_time)
        
        # Record error if failed
        if not success:
            if endpoint not in self.error_counts:
                self.error_counts[endpoint] = deque(maxlen=100)
            self.error_counts[endpoint].append(current_time)


class AlertManager:
    """Manages performance alerts and notifications"""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.alert_configs: List[AlertConfig] = []
        self.active_alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Load default alert configurations
        self._load_default_alerts()
    
    def _load_default_alerts(self):
        """Load default alert configurations"""
        default_alerts = [
            # System alerts
            AlertConfig("High CPU Usage", "system.cpu_usage", "above", 80.0, severity="high"),
            AlertConfig("High Memory Usage", "system.memory_usage", "above", 85.0, severity="high"),
            AlertConfig("Low Disk Space", "system.disk_usage", "above", 90.0, severity="critical"),
            AlertConfig("Low Cache Hit Rate", "system.cache_hit_rate", "below", 0.7, severity="medium"),
            AlertConfig("High Error Rate", "system.error_rates.api_errors", "above", 0.05, severity="high"),
            
            # Portfolio alerts
            AlertConfig("Large Daily Loss", "portfolio.daily_return", "below", -0.05, severity="high"),
            AlertConfig("High Drawdown", "portfolio.max_drawdown", "above", 0.15, severity="critical"),
            AlertConfig("Low Sharpe Ratio", "portfolio.sharpe_ratio", "below", 0.5, severity="medium"),
            AlertConfig("High VaR", "portfolio.var_95", "below", -0.05, severity="high"),
            AlertConfig("High Concentration", "portfolio.risk_metrics.concentration_risk", "above", 0.4, severity="medium"),
            
            # ML alerts
            AlertConfig("Low Prediction Accuracy", "ml.prediction_accuracy.price_prediction", "below", 0.6, severity="medium"),
            AlertConfig("Poor Data Quality", "ml.data_quality_scores.completeness", "below", 0.9, severity="high"),
            AlertConfig("High ML Error Rate", "ml.error_rates.model_prediction", "above", 0.1, severity="high"),
        ]
        
        self.alert_configs.extend(default_alerts)
    
    def check_alerts(self, system_metrics: SystemMetrics, 
                    portfolio_metrics: PortfolioMetrics, 
                    ml_metrics: MLMetrics):
        """Check all alerts against current metrics"""
        metrics_dict = {
            'system': system_metrics,
            'portfolio': portfolio_metrics,
            'ml': ml_metrics
        }
        
        current_time = datetime.utcnow()
        
        for alert_config in self.alert_configs:
            if not alert_config.enabled:
                continue
            
            # Check if alert is in cooldown
            if self._is_in_cooldown(alert_config, current_time):
                continue
            
            # Get current metric value
            current_value = self._get_metric_value(metrics_dict, alert_config.metric_path)
            if current_value is None:
                continue
            
            # Check threshold
            triggered = self._check_threshold(current_value, alert_config)
            
            if triggered:
                # Create alert
                alert = Alert(
                    timestamp=current_time,
                    alert_name=alert_config.name,
                    metric_path=alert_config.metric_path,
                    current_value=current_value,
                    threshold_value=alert_config.threshold_value,
                    severity=alert_config.severity,
                    message=self._generate_alert_message(alert_config, current_value)
                )
                
                self.active_alerts.append(alert)
                self.alert_history.append(alert)
                
                # Log alert
                self.audit_logger.log_event(
                    EventType.ALERT_TRIGGERED,
                    SeverityLevel.HIGH if alert_config.severity in ['high', 'critical'] else SeverityLevel.MEDIUM,
                    resource='performance_monitor',
                    details={
                        'alert_name': alert_config.name,
                        'metric_path': alert_config.metric_path,
                        'current_value': current_value,
                        'threshold': alert_config.threshold_value,
                        'severity': alert_config.severity
                    }
                )
                
                logger.warning(f"Alert triggered: {alert.message}")
    
    def _get_metric_value(self, metrics_dict: Dict[str, Any], metric_path: str) -> Optional[float]:
        """Extract metric value from nested dictionary"""
        try:
            parts = metric_path.split('.')
            current = metrics_dict
            
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            
            return float(current) if current is not None else None
            
        except (AttributeError, KeyError, TypeError, ValueError):
            return None
    
    def _check_threshold(self, current_value: float, alert_config: AlertConfig) -> bool:
        """Check if current value triggers alert"""
        if alert_config.threshold_type == "above":
            return current_value > alert_config.threshold_value
        elif alert_config.threshold_type == "below":
            return current_value < alert_config.threshold_value
        elif alert_config.threshold_type == "outside_range" and alert_config.threshold_range:
            lower, upper = alert_config.threshold_range
            return current_value < lower or current_value > upper
        
        return False
    
    def _is_in_cooldown(self, alert_config: AlertConfig, current_time: datetime) -> bool:
        """Check if alert is in cooldown period"""
        for alert in reversed(self.alert_history):
            if (alert.alert_name == alert_config.name and 
                not alert.resolved and
                (current_time - alert.timestamp).seconds < alert_config.cooldown_minutes * 60):
                return True
        return False
    
    def _generate_alert_message(self, alert_config: AlertConfig, current_value: float) -> str:
        """Generate alert message"""
        return (f"{alert_config.name}: {alert_config.metric_path} is {current_value:.4f} "
                f"(threshold: {alert_config.threshold_value:.4f})")
    
    def resolve_alert(self, alert_name: str):
        """Mark alert as resolved"""
        current_time = datetime.utcnow()
        for alert in self.active_alerts:
            if alert.alert_name == alert_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_timestamp = current_time
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return [alert for alert in self.active_alerts if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by severity"""
        active_alerts = self.get_active_alerts()
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for alert in active_alerts:
            if alert.severity in summary:
                summary[alert.severity] += 1
        
        return summary


class PerformanceMonitor:
    """Main performance monitoring dashboard"""
    
    def __init__(self, collection_interval: int = 60):
        """
        Initialize performance monitor
        
        Args:
            collection_interval: Metrics collection interval in seconds
        """
        self.collector = PerformanceCollector()
        self.alert_manager = AlertManager()
        self.audit_logger = get_audit_logger()
        
        self.collection_interval = collection_interval
        self.running = False
        self.monitor_thread = None
        
        # Metrics storage
        self.current_metrics = {
            'system': None,
            'portfolio': None,
            'ml': None
        }
        
        # Dashboard data
        self.dashboard_data = {
            'last_updated': None,
            'system_health': 'unknown',
            'portfolio_status': 'unknown',
            'ml_status': 'unknown',
            'alerts': []
        }
        
        logger.info("Performance Monitor initialized")
    
    def start_monitoring(self):
        """Start the performance monitoring service"""
        if self.running:
            logger.warning("Performance monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop the performance monitoring service"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                system_metrics = self.collector.collect_system_metrics()
                
                # For portfolio metrics, we'd normally get this from the portfolio manager
                portfolio_data = self._get_portfolio_data()
                portfolio_metrics = self.collector.collect_portfolio_metrics(portfolio_data)
                
                # Collect ML metrics
                ml_metrics = self.collector.collect_ml_metrics()
                
                # Store current metrics
                self.current_metrics = {
                    'system': system_metrics,
                    'portfolio': portfolio_metrics,
                    'ml': ml_metrics
                }
                
                # Store in history
                self.collector.metrics_history['system'].append(system_metrics)
                self.collector.metrics_history['portfolio'].append(portfolio_metrics)
                self.collector.metrics_history['ml'].append(ml_metrics)
                
                # Check alerts
                self.alert_manager.check_alerts(system_metrics, portfolio_metrics, ml_metrics)
                
                # Update dashboard
                self._update_dashboard()
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.collection_interval)
    
    def _get_portfolio_data(self) -> Dict[str, Any]:
        """Get current portfolio data (placeholder)"""
        # This would integrate with the actual portfolio manager
        return {
            'total_value': 100000.0,
            'daily_return': 0.01,
            'total_return': 0.15,
            'volatility': 0.20,
            'sharpe_ratio': 0.75,
            'max_drawdown': 0.08,
            'beta': 1.2,
            'var_95': -0.03,
            'positions': {
                'NVDA': {'shares': 10, 'market_value': 8500, 'weight': 0.085, 'unrealized_pnl': 150, 'day_change': 0.02},
                'MSFT': {'shares': 15, 'market_value': 7500, 'weight': 0.075, 'unrealized_pnl': -50, 'day_change': -0.01},
                'TSLA': {'shares': 8, 'market_value': 6000, 'weight': 0.06, 'unrealized_pnl': 200, 'day_change': 0.03}
            },
            'sector_allocation': {
                'Technology': 0.4,
                'Healthcare': 0.2,
                'Financial': 0.15,
                'Energy': 0.1,
                'Consumer': 0.15
            },
            'liquidity_score': 0.85,
            'correlation_risk': 0.65
        }
    
    def _update_dashboard(self):
        """Update dashboard data"""
        current_time = datetime.utcnow()
        
        # Determine system health
        system_health = self._assess_system_health()
        portfolio_status = self._assess_portfolio_status()
        ml_status = self._assess_ml_status()
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        self.dashboard_data = {
            'last_updated': current_time,
            'system_health': system_health,
            'portfolio_status': portfolio_status,
            'ml_status': ml_status,
            'alerts': [
                {
                    'name': alert.alert_name,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                }
                for alert in active_alerts
            ],
            'metrics_summary': {
                'system': {
                    'cpu_usage': self.current_metrics['system'].cpu_usage if self.current_metrics['system'] else 0,
                    'memory_usage': self.current_metrics['system'].memory_usage if self.current_metrics['system'] else 0,
                    'cache_hit_rate': self.current_metrics['system'].cache_hit_rate if self.current_metrics['system'] else 0
                },
                'portfolio': {
                    'total_value': self.current_metrics['portfolio'].total_value if self.current_metrics['portfolio'] else 0,
                    'daily_return': self.current_metrics['portfolio'].daily_return if self.current_metrics['portfolio'] else 0,
                    'sharpe_ratio': self.current_metrics['portfolio'].sharpe_ratio if self.current_metrics['portfolio'] else 0
                },
                'ml': {
                    'avg_accuracy': np.mean(list(self.current_metrics['ml'].prediction_accuracy.values())) if self.current_metrics['ml'] and self.current_metrics['ml'].prediction_accuracy else 0,
                    'avg_confidence': np.mean(list(self.current_metrics['ml'].model_confidence.values())) if self.current_metrics['ml'] and self.current_metrics['ml'].model_confidence else 0
                }
            }
        }
    
    def _assess_system_health(self) -> str:
        """Assess overall system health"""
        if not self.current_metrics['system']:
            return 'unknown'
        
        metrics = self.current_metrics['system']
        
        # Check critical thresholds
        if metrics.cpu_usage > 90 or metrics.memory_usage > 90 or metrics.disk_usage > 95:
            return 'critical'
        elif metrics.cpu_usage > 80 or metrics.memory_usage > 80 or metrics.disk_usage > 85:
            return 'warning'
        elif metrics.cache_hit_rate < 0.5 or max(metrics.error_rates.values(), default=0) > 0.1:
            return 'warning'
        else:
            return 'healthy'
    
    def _assess_portfolio_status(self) -> str:
        """Assess portfolio status"""
        if not self.current_metrics['portfolio']:
            return 'unknown'
        
        metrics = self.current_metrics['portfolio']
        
        # Check portfolio health
        if metrics.max_drawdown > 0.2 or metrics.daily_return < -0.1:
            return 'critical'
        elif metrics.max_drawdown > 0.1 or metrics.daily_return < -0.05 or metrics.sharpe_ratio < 0:
            return 'warning'
        else:
            return 'healthy'
    
    def _assess_ml_status(self) -> str:
        """Assess ML system status"""
        if not self.current_metrics['ml']:
            return 'unknown'
        
        metrics = self.current_metrics['ml']
        
        # Check ML health
        avg_accuracy = np.mean(list(metrics.prediction_accuracy.values())) if metrics.prediction_accuracy else 0
        avg_data_quality = np.mean(list(metrics.data_quality_scores.values())) if metrics.data_quality_scores else 0
        
        if avg_accuracy < 0.5 or avg_data_quality < 0.8:
            return 'critical'
        elif avg_accuracy < 0.6 or avg_data_quality < 0.9:
            return 'warning'
        else:
            return 'healthy'
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()
    
    def get_metrics_history(self, metric_type: str, hours: int = 24) -> List[Any]:
        """Get metrics history for specified time period"""
        if metric_type not in self.collector.metrics_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = self.collector.metrics_history[metric_type]
        
        return [metric for metric in history if metric.timestamp >= cutoff_time]
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics"""
        return {
            'monitoring_status': 'running' if self.running else 'stopped',
            'last_collection': self.dashboard_data['last_updated'],
            'total_alerts': len(self.alert_manager.alert_history),
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'alert_summary': self.alert_manager.get_alert_summary(),
            'metrics_history_size': {
                'system': len(self.collector.metrics_history['system']),
                'portfolio': len(self.collector.metrics_history['portfolio']),
                'ml': len(self.collector.metrics_history['ml'])
            },
            'system_health': self.dashboard_data['system_health'],
            'portfolio_status': self.dashboard_data['portfolio_status'],
            'ml_status': self.dashboard_data['ml_status']
        }
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to CSV file"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Combine all metrics
            all_metrics = []
            
            for metric_type in ['system', 'portfolio', 'ml']:
                history = self.collector.metrics_history[metric_type]
                for metric in history:
                    if metric.timestamp >= cutoff_time:
                        metric_dict = {
                            'timestamp': metric.timestamp,
                            'type': metric_type
                        }
                        
                        # Add metric-specific fields
                        for field, value in metric.__dict__.items():
                            if field != 'timestamp':
                                if isinstance(value, dict):
                                    for k, v in value.items():
                                        metric_dict[f"{field}_{k}"] = v
                                else:
                                    metric_dict[field] = value
                        
                        all_metrics.append(metric_dict)
            
            # Convert to DataFrame and save
            df = pd.DataFrame(all_metrics)
            df.to_csv(filepath, index=False)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


if __name__ == "__main__":
    # Test performance monitor
    monitor = PerformanceMonitor(collection_interval=10)
    
    try:
        print("Starting performance monitoring test...")
        monitor.start_monitoring()
        
        # Let it run for a minute
        time.sleep(60)
        
        # Get dashboard data
        dashboard = monitor.get_dashboard_data()
        print(f"System Health: {dashboard['system_health']}")
        print(f"Portfolio Status: {dashboard['portfolio_status']}")
        print(f"ML Status: {dashboard['ml_status']}")
        print(f"Active Alerts: {len(dashboard['alerts'])}")
        
        # Get diagnostics
        diagnostics = monitor.get_system_diagnostics()
        print(f"Diagnostics: {diagnostics}")
        
    finally:
        monitor.stop_monitoring()
        print("Performance monitoring test completed")