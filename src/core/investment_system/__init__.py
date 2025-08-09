"""
Investment Analysis System

AI-powered investment analysis system for AI/Robotics stocks and ETFs.
"""

__version__ = "1.0.0"
__author__ = "Ivan"

# Avoid importing submodules at package import time to minimize side effects and
# heavy dependency initialization during test collection. Consumers should import
# the needed modules directly, e.g., `from core.investment_system.ethics import ...`.

__all__ = [
    "__version__",
    "__author__",
]