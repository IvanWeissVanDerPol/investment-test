# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Automated Investment Analysis System

## Project Overview
AI-powered investment analysis system for individual trading decisions focused on AI/Robotics stocks and ETFs. Modern Python package structure with comprehensive market analysis, sentiment tracking, and automated reporting.

## Project Structure

```
ivan/
├── src/investment_system/          # Main Python package
│   ├── data/                      # Data collection modules
│   ├── analysis/                  # Analysis engines
│   ├── portfolio/                 # Portfolio management
│   ├── monitoring/                # System monitoring
│   ├── reporting/                 # Report generation
│   └── utils/                     # Utility functions
├── docs/                          # Documentation
│   ├── strategy/                  # Investment strategies
│   ├── research/                  # Broker and market research
│   ├── guides/                    # Setup and maintenance guides
│   ├── tracking/                  # Portfolio tracking docs
│   └── sectors/                   # Sector analysis docs
├── config/                        # Configuration files
├── tests/                         # Test suite
├── reports/                       # Generated analysis reports
├── cache/                         # Data cache
└── .claude/                       # Claude Code tools
    ├── commands/                  # Slash commands
    └── hooks/                     # Pre/post analysis hooks
```

## Common Commands

### Running Analysis
```bash
# Quick daily analysis (2-3 minutes)
python -m src.investment_system.analysis.quick_analysis

# Comprehensive analysis with all modules (10-15 minutes)  
python -m src.investment_system.analysis.comprehensive_analyzer

# System monitoring
python -m src.investment_system.monitoring.system_monitor

# Windows batch shortcuts
run_daily_analysis.bat
run_comprehensive_analysis.bat
run_system_monitor.bat
```

### Development Workflow
```bash
# Setup development environment
setup_dev_environment.bat

# Run all tests
python -m pytest tests/ -v
# Or use: run_tests.bat

# Code quality checks
make format     # Format code with black/isort
make lint       # Run flake8 linting
make type-check # Run mypy type checking

# Pre-analysis validation
python .claude/hooks/pre_analysis_hook.py
```

### Slash Commands (Claude Code)
- `/clean` - Format code, organize imports, fix linting issues
- `/analyze` - Comprehensive code analysis and architecture review
- `/optimize` - Performance analysis and optimization recommendations
- `/test` - Run complete test suite with coverage
- `/portfolio` - Portfolio management and analysis commands
- `/monitor` - System monitoring and health checks

## System Architecture

### Package Structure
The system uses a proper Python package structure with clear separation of concerns:

1. **Data Layer** (`src/investment_system/data/`)
   - `market_data_collector.py` - Multi-source market data aggregation
   - `news_feed.py` - Financial news ingestion
   - `data_ingestion.py` - General data processing
   - `real_time_data_manager.py` - Live data streaming

2. **Analysis Layer** (`src/investment_system/analysis/`)
   - `quick_analysis.py` - Fast technical analysis (2-3 min)
   - `comprehensive_analyzer.py` - Complete analysis orchestrator (10-15 min)
   - `advanced_market_analyzer.py` - Options flow and technical indicators
   - `ai_prediction_engine.py` - ML-based pattern recognition
   - `news_sentiment_analyzer.py` - NLP sentiment analysis
   - `social_sentiment_analyzer.py` - Social media sentiment tracking

3. **Portfolio Layer** (`src/investment_system/portfolio/`)
   - `risk_management.py` - Position sizing and risk metrics
   - `portfolio_analysis.py` - Portfolio optimization and allocation
   - `backtesting_engine.py` - Historical strategy validation
   - `smart_money_tracker.py` - Institutional investor tracking
   - `government_spending_monitor.py` - AI contract monitoring
   - `investment_signal_engine.py` - Signal generation and aggregation

4. **Monitoring Layer** (`src/investment_system/monitoring/`)
   - `system_monitor.py` - Continuous system health monitoring
   - `alert_system.py` - Threshold-based notifications

5. **Reporting Layer** (`src/investment_system/reporting/`)
   - `automated_reporter.py` - Multi-format report generation

6. **Utils Layer** (`src/investment_system/utils/`)
   - `cache_manager.py` - Data caching and performance optimization

### Configuration System
- **`config/config.json`** - Central configuration
  - User profile (Ivan, $900 balance, medium risk tolerance)
  - Target assets: AI/Robotics stocks and ETFs
  - Alert thresholds and API settings
  - Smart money tracking targets (ARK, Tiger Global, Coatue, etc.)

### Data Flow
```
External APIs → Data Collection → Analysis Engines → Portfolio Management
     ↓              ↓                  ↓                    ↓
Cache Layer → Real-time Processing → Signal Generation → Risk Assessment
     ↓              ↓                  ↓                    ↓  
Performance → Sentiment Analysis → Portfolio Optimization → Reports & Alerts
```

## Import Patterns

### Modern Package Imports
```python
# Analysis modules
from src.investment_system.analysis import get_stock_analysis, ComprehensiveAnalyzer
from src.investment_system.portfolio import RiskManager, PortfolioAnalyzer
from src.investment_system.data import MarketDataCollector
from src.investment_system.utils import CacheManager

# Direct module access
import src.investment_system.analysis.quick_analysis
import src.investment_system.monitoring.system_monitor
```

### Configuration Loading
```python
import json
from pathlib import Path

config_path = Path("config/config.json")
with open(config_path, 'r') as f:
    config = json.load(f)
```

## Key Design Patterns

### Package-Based Architecture
- Clear separation of concerns with dedicated packages
- Proper `__init__.py` files with controlled exports
- Consistent import patterns across modules
- Module-level documentation and version tracking

### Configuration-Driven Development
- Centralized configuration in `config/config.json`
- Environment-specific settings support
- Validation hooks for configuration changes

### Hook-Based Quality Control
- Pre-analysis validation hooks
- Post-analysis verification and notifications
- Automated code quality enforcement
- Investment-specific validation rules

## Investment Focus Areas
- **Primary Stocks**: NVDA, MSFT, TSLA, DE, TSM, AMZN, GOOGL, META, AAPL, CRM
- **AI/Robotics ETFs**: KROP, BOTZ, SOXX, ARKQ, ROBO, IRBO, UBOT
- **Smart Money Tracking**: ARK Invest, Tiger Global, Coatue, Whale Rock, Berkshire Hathaway
- **Government Contracts**: Defense contractors and AI-focused government spending
- **Portfolio**: $900 balance, medium risk tolerance, quarterly rebalancing

## Development Guidelines
- Use proper package imports (`src.investment_system.*`)
- Maintain configuration accuracy in `config/config.json`
- Run pre-analysis validation before major operations
- All modules include comprehensive error handling
- Reports include confidence scores and risk warnings
- Follow hooks-based development workflow
- Use Claude Code slash commands for common operations