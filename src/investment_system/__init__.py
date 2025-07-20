"""
Investment Analysis System

AI-powered investment analysis system for AI/Robotics stocks and ETFs.
"""

__version__ = "1.0.0"
__author__ = "Ivan"

from .utils.cache_manager import CacheManager
from .data.market_data_collector import MarketDataCollector
from .analysis.quick_analysis import get_stock_analysis
from .portfolio.risk_management import RiskManager

__all__ = [
    "CacheManager",
    "MarketDataCollector", 
    "get_stock_analysis",
    "RiskManager"
]