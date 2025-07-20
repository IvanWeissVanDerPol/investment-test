"""Portfolio management and optimization"""

from .risk_management import RiskManager
from .portfolio_analysis import PortfolioAnalyzer
from .investment_signal_engine import InvestmentSignalEngine
from .smart_money_tracker import SmartMoneyTracker
from .government_spending_monitor import GovernmentSpendingMonitor
from .backtesting_engine import BacktestingEngine

__all__ = [
    "RiskManager",
    "PortfolioAnalyzer",
    "InvestmentSignalEngine",
    "SmartMoneyTracker",
    "GovernmentSpendingMonitor",
    "BacktestingEngine"
]