# Context Priming for Investment Analysis System

Load comprehensive project context to understand the investment analysis system architecture, current portfolio status, and analysis workflows.

## Context Loading Steps:

### 1. Project Structure Overview
```bash
# Show complete project structure
tree /f C:\Users\jandr\Documents\ivan
```

### 2. Load Key Configuration
```bash
# Display current portfolio configuration
type config\config.json
```

### 3. Review Recent Analysis Results
```bash
# Show latest investment analysis reports
dir reports\*.json /od | tail -5
```

### 4. Check System Status
```bash
# Validate system health
python .claude\hooks\pre_analysis_hook.py
```

### 5. Load Investment Focus Context
Review the following key areas:

**Portfolio Status:**
- Balance: $900 (Dukascopy)
- Risk Tolerance: Medium
- Focus: AI/Robotics stocks and ETFs
- Rebalancing: Quarterly (Next: Oct 1, 2025)

**Target Assets:**
- **Primary Stocks**: NVDA, MSFT, TSLA, DE, TSM, AMZN, GOOGL, META, AAPL, CRM
- **AI/Robotics ETFs**: KROP, BOTZ, SOXX, ARKQ, ROBO, IRBO, UBOT

**Smart Money Tracking:**
- ARK Invest, Tiger Global Management, Coatue Management
- Whale Rock Capital, Berkshire Hathaway, Bridgewater Associates

**Analysis Modules:**
- Quick Analysis (2-3 min): `src/investment_system/analysis/quick_analysis.py`
- Comprehensive Analysis (10-15 min): `src/investment_system/analysis/comprehensive_analyzer.py`
- News Sentiment: `src/investment_system/analysis/news_sentiment_analyzer.py`
- Social Sentiment: `src/investment_system/analysis/social_sentiment_analyzer.py`
- Risk Management: `src/investment_system/portfolio/risk_management.py`

### 6. Current Market Context
Load understanding of:
- Current market conditions for AI/Robotics sector
- Recent performance of target stocks and ETFs
- Government contract activity in AI space
- Institutional investor movements

## Ready State Confirmation
After context loading, confirm understanding of:
1. ✅ Project architecture and module organization
2. ✅ Current portfolio composition and targets
3. ✅ Available analysis tools and their purposes
4. ✅ Risk management parameters and constraints
5. ✅ Investment strategy focus areas

## Usage
This command prepares Claude with comprehensive context about the investment analysis system, enabling more informed and targeted assistance with analysis, strategy, and system improvements.