"""
Enhanced Logger for Investment Analysis
Provides colored output, structured logging, and analysis-specific formatting
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

class ColorFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'ANALYSIS': '\033[34m',   # Blue
        'SUCCESS': '\033[92m',    # Bright Green
        'HIGHLIGHT': '\033[93m',  # Bright Yellow
        'RESET': '\033[0m'        # Reset
    }
    
    # Investment-specific symbols
    SYMBOLS = {
        'BUY': '📈',
        'SELL': '📉',
        'HOLD': '➡️',
        'ALERT': '🚨',
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️',
        'MONEY': '💰',
        'CHART': '📊',
        'NEWS': '📰',
        'ROBOT': '🤖'
    }
    
    def format(self, record):
        # Add color to the log level
        if hasattr(record, 'use_colors') and record.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # Add symbols for special message types
        if hasattr(record, 'symbol'):
            record.msg = f"{self.SYMBOLS.get(record.symbol, '')} {record.msg}"
        
        return super().format(record)

class InvestmentLogger:
    """Enhanced logger for investment analysis with structured output"""
    
    def __init__(self, name: str = "investment_system", config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        
        # Load settings from config
        output_settings = self.config.get('analysis_settings', {}).get('output_settings', {})
        self.use_colors = output_settings.get('console_colors', True)
        self.detailed_logging = output_settings.get('detailed_logging', True)
        self.show_timestamps = output_settings.get('show_timestamps', True)
        self.log_level = output_settings.get('log_level', 'INFO')
        
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with appropriate handlers and formatters"""
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Format string
        if self.show_timestamps:
            format_str = '%(asctime)s | %(levelname)-8s | %(message)s'
            date_format = '%H:%M:%S'
        else:
            format_str = '%(levelname)-8s | %(message)s'
            date_format = None
        
        # Apply color formatter
        formatter = ColorFormatter(format_str, datefmt=date_format)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logs
        if self.detailed_logging:
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f'investment_analysis_{datetime.now().strftime("%Y%m%d")}.log'
            )
            file_handler.setLevel(logging.DEBUG)
            
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def _log_with_extras(self, level: str, message: str, symbol: Optional[str] = None, **kwargs):
        """Internal method to log with extra attributes"""
        extra = {'use_colors': self.use_colors}
        if symbol:
            extra['symbol'] = symbol
        
        getattr(self.logger, level.lower())(message, extra=extra, **kwargs)
    
    # Standard logging methods
    def debug(self, message: str, **kwargs):
        self._log_with_extras('DEBUG', message, **kwargs)
    
    def info(self, message: str, symbol: Optional[str] = None, **kwargs):
        self._log_with_extras('INFO', message, symbol, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_extras('WARNING', message, 'WARNING', **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_extras('ERROR', message, 'ERROR', **kwargs)
    
    def success(self, message: str, **kwargs):
        self._log_with_extras('INFO', message, 'SUCCESS', **kwargs)
    
    # Investment-specific logging methods
    def analysis_start(self, analysis_type: str, symbols: list = None):
        """Log the start of an analysis"""
        symbol_str = f" for {', '.join(symbols)}" if symbols else ""
        self.info(f"Starting {analysis_type} analysis{symbol_str}", symbol='ROBOT')
    
    def analysis_complete(self, analysis_type: str, duration: float = None):
        """Log the completion of an analysis"""
        duration_str = f" (completed in {duration:.2f}s)" if duration else ""
        self.success(f"{analysis_type} analysis completed{duration_str}")
    
    def stock_recommendation(self, symbol: str, action: str, confidence: float, price: float = None):
        """Log a stock recommendation"""
        action_upper = action.upper()
        symbol_emoji = {
            'STRONG_BUY': 'BUY',
            'BUY': 'BUY', 
            'HOLD': 'HOLD',
            'SELL': 'SELL',
            'STRONG_SELL': 'SELL'
        }.get(action_upper, 'INFO')
        
        price_str = f" at ${price:.2f}" if price else ""
        confidence_str = f" (confidence: {confidence:.1%})"
        
        self.info(
            f"{symbol}: {action_upper}{price_str}{confidence_str}",
            symbol=symbol_emoji
        )
    
    def portfolio_update(self, message: str):
        """Log portfolio-related updates"""
        self.info(message, symbol='MONEY')
    
    def market_alert(self, message: str):
        """Log market alerts"""
        self.warning(message, symbol='ALERT')
    
    def news_update(self, message: str):
        """Log news-related updates"""
        self.info(message, symbol='NEWS')
    
    def chart_analysis(self, message: str):
        """Log chart/technical analysis"""
        self.info(message, symbol='CHART')
    
    def print_separator(self, title: Optional[str] = None, width: int = 60):
        """Print a separator line with optional title"""
        if title:
            title_formatted = f" {title} "
            padding = (width - len(title_formatted)) // 2
            line = "=" * padding + title_formatted + "=" * padding
            if len(line) < width:
                line += "="
        else:
            line = "=" * width
        
        print(line)
    
    def print_analysis_summary(self, data: Dict[str, Any]):
        """Print a structured analysis summary"""
        self.print_separator("ANALYSIS SUMMARY")
        
        # Format and display key metrics
        if 'timestamp' in data:
            self.info(f"Analysis Time: {data['timestamp']}")
        
        if 'portfolio_value' in data:
            self.portfolio_update(f"Portfolio Value: ${data['portfolio_value']:,.2f}")
        
        if 'recommendations' in data:
            self.print_separator("RECOMMENDATIONS")
            for rec in data['recommendations']:
                self.stock_recommendation(
                    rec.get('symbol', 'Unknown'),
                    rec.get('action', 'HOLD'),
                    rec.get('confidence', 0.0),
                    rec.get('price')
                )
        
        if 'alerts' in data:
            self.print_separator("ALERTS")
            for alert in data['alerts']:
                self.market_alert(alert)
        
        self.print_separator()
    
    def log_config_validation(self, config_status: Dict[str, Any]):
        """Log configuration validation results"""
        self.print_separator("CONFIGURATION STATUS")
        
        for component, status in config_status.items():
            if status.get('valid', False):
                self.success(f"{component}: {status.get('message', 'OK')}")
            else:
                self.error(f"{component}: {status.get('message', 'Failed')}")
        
        self.print_separator()

# Global logger instance
_global_logger = None

def get_logger(name: str = "investment_system", config: Optional[Dict] = None) -> InvestmentLogger:
    """Get or create a global logger instance"""
    global _global_logger
    
    if _global_logger is None or config is not None:
        _global_logger = InvestmentLogger(name, config)
    
    return _global_logger

def setup_logging(config: Optional[Dict] = None):
    """Setup global logging configuration"""
    global _global_logger
    _global_logger = InvestmentLogger("investment_system", config)
    return _global_logger