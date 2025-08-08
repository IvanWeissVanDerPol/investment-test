"""Report generation and output"""

# Import available reporters
try:
    from .automated_reporter import AutomatedReporter
    AUTOMATED_REPORTER_AVAILABLE = True
except ImportError:
    AUTOMATED_REPORTER_AVAILABLE = False

from .ai_sustainability_reporter import AISustainabilityReporter

__all__ = [
    "AISustainabilityReporter"
]

if AUTOMATED_REPORTER_AVAILABLE:
    __all__.append("AutomatedReporter")