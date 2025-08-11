"""
Sonar subsystem for code analysis and AI context optimization.
Provides dependency graph and security-hardened context slicing.
"""

from .indexer import SonarIndexer, SonarGraph
from .api import SonarAPI, get_sonar_api
from .security import AISecurityGuard, ContextGuard, ai_security_guard, context_guard

__all__ = [
    "SonarIndexer",
    "SonarGraph",
    "SonarAPI",
    "get_sonar_api",
    "AISecurityGuard",
    "ContextGuard",
    "ai_security_guard",
    "context_guard"
]