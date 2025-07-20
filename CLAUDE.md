# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Automated Investment Analysis System

## Project Overview
AI-powered investment analysis system for individual trading decisions focused on AI/Robotics stocks and ETFs. Python-based modular architecture with comprehensive market analysis, sentiment tracking, and automated reporting.

## Common Commands

### Running Analysis
```bash
# Quick daily analysis (2-3 minutes)
cd tools && python quick_analysis.py

# Comprehensive analysis with all modules (10-15 minutes)
cd tools && python comprehensive_analyzer.py

# Windows batch shortcuts
run_daily_analysis.bat
run_comprehensive_analysis.bat
```

### Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Key dependencies: pandas, yfinance, requests, beautifulsoup4, newsapi-python
```

### Testing Analysis Tools
```bash
# Test individual modules
cd tools
python -c "from quick_analysis import get_stock_analysis; print(get_stock_analysis('NVDA'))"
python -c "from news_sentiment_analyzer import NewsSentimentAnalyzer; analyzer = NewsSentimentAnalyzer(); print('News analyzer ready')"
```

## System Architecture

### Core Analysis Pipeline
The system follows a modular pipeline architecture:

1. **Data Collection Layer** (`market_data_collector.py`, `news_feed.py`)
   - Multi-source market data aggregation
   - News and sentiment data ingestion
   - Smart money tracking via institutional filings

2. **Analysis Engine Layer**
   - `quick_analysis.py` - Fast technical analysis with basic signals
   - `comprehensive_analyzer.py` - Master orchestrator integrating all modules
   - `advanced_market_analyzer.py` - Options flow and technical indicators
   - `ai_prediction_engine.py` - ML-based pattern recognition
   - `news_sentiment_analyzer.py` - NLP sentiment analysis
   - `social_sentiment_analyzer.py` - Social media sentiment tracking

3. **Risk & Portfolio Management**
   - `risk_management.py` - Position sizing and risk metrics
   - `backtesting_engine.py` - Historical strategy validation
   - `alert_system.py` - Threshold-based notifications

4. **Reporting & Output**
   - `automated_reporter.py` - Multi-format report generation
   - Reports generated in JSON and human-readable formats in `reports/`

### Configuration System
- **`tools/config.json`** - Central configuration hub
  - User profile (Ivan, $900 balance, medium risk tolerance)
  - Target assets and sectors
  - Alert thresholds and API settings
  - Smart money tracking targets (ARK, Tiger Global, Coatue, etc.)

### Data Flow
```
Market Data → Analysis Modules → Risk Assessment → Portfolio Recommendations → Reports
     ↓              ↓                    ↓                      ↓               ↓
Cache Layer → Sentiment Engine → Signal Generation → Position Sizing → JSON/Text Output
```

## Key Design Patterns

### Modular Analyzer Pattern
Each analyzer follows the same interface:
- `__init__(config_file)` - Load configuration
- Main analysis method returning standardized data structure
- Error handling with graceful degradation
- Caching layer integration via `cache_manager.py`

### Report Generation Pattern
All analysis outputs follow consistent structure:
- Timestamp and analysis type metadata
- Confidence scores (0.0-1.0) for all recommendations
- Risk warnings and position sizing suggestions
- Both machine-readable JSON and human-readable summaries

### Configuration-Driven Development
System behavior controlled through `config.json`:
- Target stocks/ETFs lists
- Alert thresholds
- API endpoints and keys
- User profile parameters

## Investment Focus Areas
- **Primary Stocks**: NVDA, MSFT, TSLA, DE, TSM, AMZN, GOOGL, META, AAPL, CRM
- **AI/Robotics ETFs**: KROP, BOTZ, SOXX, ARKQ, ROBO, IRBO, UBOT
- **Smart Money Tracking**: ARK Invest, Tiger Global, Coatue, Whale Rock, Berkshire Hathaway
- **Government Contracts**: Defense contractors and AI-focused government spending

## Development Guidelines
- Always test analysis modules before deploying changes
- Maintain configuration accuracy in `tools/config.json`
- Reports must include confidence scores and risk warnings
- Use caching layer for expensive API calls
- Follow modular pattern for new analyzers