"""Portfolio management and optimization"""

from .risk_management import RiskManager
from .investment_signal_engine import InvestmentSignalEngine
from .smart_money_tracker import SmartMoneyTracker
from .government_spending_monitor import GovernmentSpendingMonitor
from .backtesting_engine import BacktestingEngine

__all__ = [
    "RiskManager",
    "InvestmentSignalEngine",
    "SmartMoneyTracker",
    "GovernmentSpendingMonitor",
    "BacktestingEngine"
]