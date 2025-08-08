from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Position:
    """Represents a single stock position in the portfolio."""
    symbol: str
    name: str
    sector: str
    industry: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    market_cap: str
    
    @property
    def weight_percent(self) -> float:
        """Calculate position weight as percentage of total portfolio."""
        # This will be calculated based on total portfolio value
        return 0.0

@dataclass
class PortfolioSummary:
    """Represents overall portfolio summary."""
    total_value: float
    available_cash: float
    invested_amount: float
    daily_change: float
    daily_change_percent: float
    ai_allocation_percent: float
    green_allocation_percent: float
    total_return: float
    total_return_percent: float
    last_updated: datetime

@dataclass
class SectorAllocation:
    """Represents allocation by sector."""
    sector: str
    total_value: float
    percentage: float
    avg_performance: float
    
@dataclass
class RiskMetrics:
    """Portfolio risk metrics."""
    portfolio_beta: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    
@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics."""
    total_return: float
    ytd_return: float
    one_month_return: float
    three_month_return: float
    one_year_return: float
    best_performer: str
    worst_performer: str