"""
AI Module for Investment Analysis
Provides Claude-powered investment insights and decision support with YouTube intelligence
"""

from .claude_client import ClaudeInvestmentClient
from .investment_decision_engine import AIInvestmentDecisionEngine
from .enhanced_investment_decision_engine import EnhancedAIInvestmentDecisionEngine, get_enhanced_decision_engine

# Make classes available at package level
__all__ = [
    'ClaudeInvestmentClient',
    'AIInvestmentDecisionEngine', 
    'EnhancedAIInvestmentDecisionEngine',
    'get_enhanced_decision_engine'
]

# Version info
__version__ = '2.0.0'