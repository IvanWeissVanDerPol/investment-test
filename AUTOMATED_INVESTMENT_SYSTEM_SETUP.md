# Automated Investment Research System Setup Guide

## Overview
Complete automated investment research system that tracks smart money, government spending, market data, and generates actionable investment signals.

## System Components

### 1. Smart Money Tracker (`smart_money_tracker.py`)
- Monitors institutional investors and hedge funds
- Tracks insider trading activity
- Analyzes SEC filings and 13F forms
- Generates confidence scores for institutional movements

### 2. Market Data Collector (`market_data_collector.py`)
- Real-time stock price data via yFinance
- Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- Sector performance analysis
- ETF analysis and recommendations
- Volume and momentum indicators

### 3. Government Spending Monitor (`government_spending_monitor.py`)
- USASpending.gov API integration
- DARPA program tracking
- Defense budget allocation analysis
- AI/robotics contract monitoring
- Investment impact assessment

### 4. Investment Signal Engine (`investment_signal_engine.py`)
- Combines all data sources into weighted signals
- Generates BUY/SELL/HOLD recommendations
- Calculates target prices and stop losses
- Risk assessment and position sizing
- Confidence scoring and priority ranking

### 5. Automated Reporter (`automated_reporter.py`)
- Orchestrates all modules
- Generates daily investment reports
- Email notifications (configurable)
- Scheduled automation
- Human-readable summaries

## Installation Instructions

### Prerequisites
- Python 3.8+
- Node.js (for MCP servers)
- Claude Code CLI

### Step 1: Install Python Dependencies
```bash
cd C:\Users\jandr\Documents\ivan
pip install -r requirements.txt
```

### Step 2: MCP Servers (Already Installed)
The following MCP servers are installed for enhanced web scraping:
- `filesystem` - File operations
- `puppeteer` - Web scraping and automation
- `fetch` - HTTP requests
- `browser-tools` - Advanced browser automation

### Step 3: Configuration
Create `config.json` in the tools directory:

```json
{
  "alpha_vantage": {
    "api_key": "YOUR_ALPHA_VANTAGE_API_KEY",
    "base_url": "https://www.alphavantage.co/query"
  },
  "email_settings": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your_email@gmail.com",
    "password": "your_app_password",
    "recipient": "recipient@gmail.com"
  },
  "target_stocks": [
    "NVDA", "MSFT", "TSLA", "DE", "TSM",
    "AMZN", "GOOGL", "META", "AAPL", "CRM"
  ],
  "ai_robotics_etfs": [
    "KROP", "BOTZ", "SOXX", "ARKQ", "ROBO"
  ],
  "alert_thresholds": {
    "strong_buy_confidence": 0.8,
    "price_movement_alert": 0.05,
    "volume_spike_threshold": 2.0,
    "contract_value_alert": 50000000
  }
}
```

### Step 4: Create Reports Directory
```bash
mkdir C:\Users\jandr\Documents\ivan\reports
```

## Usage

### Manual Execution
Run individual modules:

```bash
# Generate market analysis
cd C:\Users\jandr\Documents\ivan\tools
python market_data_collector.py

# Track smart money
python smart_money_tracker.py

# Monitor government spending
python government_spending_monitor.py

# Generate investment signals
python investment_signal_engine.py

# Full automated report
python automated_reporter.py
```

### Scheduled Automation
Start the automated system:

```bash
python automated_reporter.py --schedule
```

This will:
- Generate daily reports at 8:00 AM
- Send email notifications (if configured)
- Run continuously with scheduled checks

### One-Time Report Generation
```bash
python automated_reporter.py
```

## Output Files

Reports are saved to `C:\Users\jandr\Documents\ivan\reports\`:

- `daily_investment_report_YYYYMMDD_HHMMSS.json` - Full JSON report
- `daily_summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary
- `market_report_YYYYMMDD_HHMMSS.json` - Market data analysis
- `smart_money_report_YYYYMMDD_HHMMSS.json` - Institutional activity
- `government_intel_report_YYYYMMDD_HHMMSS.json` - Government spending analysis
- `investment_signals_YYYYMMDD_HHMMSS.json` - Buy/sell signals

## Key Features

### Investment Signals
- **STRONG_BUY**: High confidence (>70%), multiple positive indicators
- **BUY**: Medium-high confidence (>60%), positive technical/fundamental signals
- **HOLD**: Neutral signals, no clear direction
- **SELL**: Negative indicators, consider reducing position
- **STRONG_SELL**: High confidence negative signals

### Risk Assessment
- **Low Risk**: Stable stocks, high confidence signals
- **Medium Risk**: Moderate volatility, mixed signals
- **High Risk**: High volatility, uncertain signals

### Data Sources
- **Technical**: Price action, volume, technical indicators
- **Smart Money**: Institutional flows, insider trading
- **Government**: AI contracts, defense spending, DARPA programs
- **Fundamental**: P/E ratios, market cap, financial health

## Alert System

### Automatic Alerts
- Strong buy signals above confidence threshold
- Significant price movements (>5%)
- High volume spikes (>2x average)
- Large government contracts (>$50M)
- Institutional buying/selling activity

### Email Notifications
Configure email settings in `config.json` to receive:
- Daily investment summaries
- Real-time alerts for high-priority signals
- Weekly performance reviews

## API Keys Required

### Free APIs (No Key Required)
- yFinance - Real-time stock data
- SEC EDGAR - Government filings and institutional data
- USASpending.gov - Government contract data

### Optional Paid APIs
- Alpha Vantage - Enhanced market data
- Polygon.io - Real-time data feeds
- WhaleWisdom - Professional institutional tracking

## Customization

### Adding New Stocks
Edit `target_stocks` in `config.json`:
```json
"target_stocks": ["NVDA", "MSFT", "YOUR_STOCK"]
```

### Adjusting Signal Weights
Modify weights in `investment_signal_engine.py`:
```python
self.weights = {
    'technical': 0.25,
    'smart_money': 0.30,
    'fundamental': 0.20,
    'government': 0.15,
    'sentiment': 0.10
}
```

### Custom Alert Thresholds
Update `alert_thresholds` in config:
```json
"alert_thresholds": {
    "strong_buy_confidence": 0.8,
    "price_movement_alert": 0.05
}
```

## Troubleshooting

### Common Issues
1. **Missing Dependencies**: Run `pip install -r requirements.txt`
2. **API Rate Limits**: Add delays between requests
3. **File Permissions**: Ensure write access to reports directory
4. **Email Issues**: Check SMTP settings and app passwords

### Log Files
Check console output for detailed logging information. All modules use Python logging for debugging.

### Performance Optimization
- Reduce target stock list for faster execution
- Adjust API call frequencies to avoid rate limits
- Use local caching for frequently accessed data

## Security Notes

- Store API keys in environment variables or secure config files
- Don't commit sensitive data to version control
- Use app-specific passwords for email notifications
- Regularly rotate API keys

## Legal Disclaimer

This system is for educational and research purposes only. Not financial advice. Always conduct your own research and consult with financial professionals before making investment decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Automated Investment System                  │
├─────────────────────────────────────────────────────────────┤
│  Data Collection Layer                                      │
│  ├── Smart Money Tracker (SEC, Institutional)              │
│  ├── Market Data Collector (Technical, Price)              │
│  ├── Government Monitor (Contracts, Spending)              │
│  └── News Sentiment (Headlines, Analysis)                  │
├─────────────────────────────────────────────────────────────┤
│  Analysis Engine                                           │
│  ├── Signal Generation (Buy/Sell/Hold)                     │
│  ├── Risk Assessment (Low/Medium/High)                     │
│  ├── Portfolio Optimization (Allocation)                   │
│  └── Confidence Scoring (0-100%)                          │
├─────────────────────────────────────────────────────────────┤
│  Reporting & Automation                                    │
│  ├── Daily Reports (JSON + Human Readable)                 │
│  ├── Email Notifications (Alerts + Summaries)             │
│  ├── Scheduled Execution (Cron-like)                      │
│  └── Historical Tracking (Performance)                     │
└─────────────────────────────────────────────────────────────┘
```

This system provides comprehensive automation for investment research, combining multiple data sources to generate actionable investment signals with confidence scoring and risk assessment.