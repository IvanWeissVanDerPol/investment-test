"""
AI Module for Investment Analysis
Provides Claude-powered investment insights and decision support
"""

from .claude_client import ClaudeInvestmentClient

# Make ClaudeInvestmentClient available at package level
__all__ = ['ClaudeInvestmentClient']

# Version info
__version__ = '1.0.0'