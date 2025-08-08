"""
Ethics System for Investment Analysis
Provides comprehensive ESG screening and green investment prioritization
"""

from .investment_blacklist import (
    InvestmentBlacklistManager,
    BlacklistCategory,
    WhitelistCategory,
    PriorityLevel,
    WhitelistEntry
)

__all__ = [
    'InvestmentBlacklistManager',
    'BlacklistCategory',
    'WhitelistCategory', 
    'PriorityLevel',
    'WhitelistEntry'
]

__version__ = '1.0.0'