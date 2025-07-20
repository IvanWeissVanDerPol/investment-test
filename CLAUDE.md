# Automated Investment Analysis System

## Project Overview
This is an AI-powered investment analysis system for individual trading decisions focused on AI/Robotics stocks and ETFs.

## Key Components
- **Analysis Tools**: `tools/` directory contains Python scripts for market analysis
- **Configuration**: `tools/config.json` contains user profile and API settings
- **Reports**: Generated in `reports/` directory with JSON and text summaries

## User Profile
- Name: Ivan
- Balance: $900 (Dukascopy)
- Focus: AI/Robotics, Government contracts, Smart money following
- Risk Tolerance: Medium

## Main Scripts
- `quick_analysis.py` - Daily 2-3 minute analysis
- `comprehensive_analyzer.py` - Deep 5-10 minute analysis
- `news_sentiment_analyzer.py` - News sentiment tracking
- `social_sentiment_analyzer.py` - Social media sentiment

## Target Assets
**Stocks**: NVDA, MSFT, TSLA, DE, TSM, AMZN, GOOGL, META, AAPL, CRM
**ETFs**: KROP, BOTZ, SOXX, ARKQ, ROBO, IRBO, UBOT

## Development Guidelines
- Always test analysis tools before recommending changes
- Maintain user profile accuracy in config.json
- Keep API keys secure (currently using demo keys)
- Generate both JSON and human-readable reports

## Important Notes
- This is for personal investment research only
- All analysis includes confidence scores and risk warnings
- Portfolio allocations consider available capital and risk management