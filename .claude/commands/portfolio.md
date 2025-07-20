# Portfolio Management Assistant

Comprehensive portfolio analysis and management commands for the $900 investment analysis system.

## Portfolio Analysis Commands:

### Current Portfolio Status
Analyze current portfolio allocation and performance:

```bash
cd tools
python -c "
from quick_analysis import get_stock_analysis
import json

# Load current portfolio from config
with open('config.json', 'r') as f:
    config = json.load(f)

print('=== CURRENT PORTFOLIO STATUS ===')
print(f'Available Balance: ${config[\"user_profile\"][\"dukascopy_balance\"]}')
print(f'Risk Tolerance: {config[\"user_profile\"][\"risk_tolerance\"]}')
print()

# Analyze target stocks
print('TARGET STOCKS ANALYSIS:')
for symbol in config['target_stocks'][:5]:  # First 5 stocks
    analysis = get_stock_analysis(symbol)
    if analysis:
        print(f'{symbol}: ${analysis[\"current_price\"]:.2f} ({analysis[\"day_change_pct\"]:+.2f}%)')
"
```

### Optimal Allocation Calculator
Calculate optimal portfolio allocation for current balance:

```bash
cd tools
python -c "
import json
import yfinance as yf

with open('config.json', 'r') as f:
    config = json.load(f)

balance = config['user_profile']['dukascopy_balance']
target_stocks = config['target_stocks'][:10]  # Top 10 targets

print(f'=== OPTIMAL ALLOCATION FOR ${balance} ===')
print()

# Equal weight allocation
allocation_per_stock = balance / len(target_stocks)
print(f'Equal Weight: ${allocation_per_stock:.2f} per stock')
print()

# Risk-adjusted allocation (medium risk)
high_conviction = ['NVDA', 'MSFT', 'TSLA']  # 60% allocation
medium_conviction = [s for s in target_stocks if s not in high_conviction]

high_allocation = (balance * 0.6) / len(high_conviction)
medium_allocation = (balance * 0.4) / len(medium_conviction) if medium_conviction else 0

print('RISK-ADJUSTED ALLOCATION:')
for stock in high_conviction:
    print(f'{stock}: ${high_allocation:.2f} (High conviction)')

for stock in medium_conviction[:4]:  # Limit medium conviction
    print(f'{stock}: ${medium_allocation:.2f} (Medium conviction)')
"
```

### Portfolio Rebalancing
Check if portfolio needs rebalancing based on target allocations:

```bash
cd tools
python -c "
import json
from datetime import datetime

print(f'=== PORTFOLIO REBALANCING CHECK ===')
print(f'Date: {datetime.now().strftime(\"%Y-%m-%d %H:%M\")}')
print()

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Check rebalancing triggers
balance = config['user_profile']['dukascopy_balance']
risk_tolerance = config['user_profile']['risk_tolerance']

print(f'Available Balance: ${balance}')
print(f'Risk Tolerance: {risk_tolerance}')
print()

# Rebalancing recommendations
print('REBALANCING RECOMMENDATIONS:')
if balance < 1000:
    print('• Focus on 3-5 high-conviction positions')
    print('• Minimize transaction costs with larger positions')
    print('• Consider ETFs for broader diversification')
else:
    print('• Can support 8-10 individual positions')
    print('• Add sector diversification')
    print('• Include both growth and value positions')

print()
print('Next scheduled rebalancing: Quarterly (Oct 1, 2025)')
"
```

## Risk Management Commands:

### Risk Assessment
Evaluate current portfolio risk levels:

```bash
cd tools
python risk_management.py --portfolio-check --balance=900
```

### Position Sizing Calculator
Calculate appropriate position sizes based on risk tolerance:

```bash
cd tools
python -c "
import json

with open('config.json', 'r') as f:
    config = json.load(f)

balance = config['user_profile']['dukascopy_balance']
risk_tolerance = config['user_profile']['risk_tolerance']

print('=== POSITION SIZING CALCULATOR ===')
print(f'Portfolio: ${balance}')
print(f'Risk Tolerance: {risk_tolerance}')
print()

# Position sizing rules for medium risk
max_single_position = balance * 0.25  # Max 25% per position
min_position_size = balance * 0.05   # Min 5% to make it worthwhile

print(f'Maximum single position: ${max_single_position:.2f} (25%)')
print(f'Minimum position size: ${min_position_size:.2f} (5%)')
print(f'Recommended positions: 6-8 stocks + 2-3 ETFs')
print()

# Specific recommendations
print('RECOMMENDED POSITION SIZES:')
print(f'High conviction (NVDA, MSFT): ${balance * 0.20:.2f} each (20%)')
print(f'Medium conviction stocks: ${balance * 0.10:.2f} each (10%)')
print(f'ETF positions (KROP, BOTZ): ${balance * 0.15:.2f} each (15%)')
"
```

## Market Analysis Commands:

### Daily Market Check
Quick market overview for investment decisions:

```bash
cd tools
python quick_analysis.py | grep -E "(NVDA|MSFT|TSLA|KROP|BOTZ)"
```

### Sector Performance
Analyze AI/Robotics sector performance:

```bash
cd tools
python -c "
import yfinance as yf
import json

with open('config.json', 'r') as f:
    config = json.load(f)

print('=== AI/ROBOTICS SECTOR PERFORMANCE ===')
print()

# AI/Robotics ETFs
etfs = config['ai_robotics_etfs'][:5]
for etf in etfs:
    try:
        ticker = yf.Ticker(etf)
        hist = ticker.history(period='5d')
        if not hist.empty:
            change = ((hist['Close'][-1] / hist['Close'][0]) - 1) * 100
            print(f'{etf}: {change:+.2f}% (5-day)')
    except:
        print(f'{etf}: Data unavailable')
"
```

## Smart Money Tracking:

### Institutional Activity
Check institutional investor activity in target stocks:

```bash
cd tools
python smart_money_tracker.py --funds="ARK Invest,Tiger Global" --stocks="NVDA,MSFT,TSLA"
```

### Government Contract Monitor
Monitor AI-related government contracts:

```bash
cd tools
python government_spending_monitor.py --ai-keywords --contracts-threshold=50000000
```

## Reports and Notifications:

### Generate Portfolio Report
Create comprehensive portfolio analysis report:

```bash
cd tools
python comprehensive_analyzer.py --portfolio-focus --balance=900
```

### Performance Summary
Get quick performance metrics:

```bash
cd tools
python -c "
import json
from pathlib import Path
from datetime import datetime

# Find latest report
reports_dir = Path('../reports')
latest_reports = sorted(reports_dir.glob('*summary*.txt'), 
                       key=lambda f: f.stat().st_mtime, reverse=True)

if latest_reports:
    print('=== LATEST PERFORMANCE SUMMARY ===')
    with open(latest_reports[0], 'r') as f:
        content = f.read()
    print(content[:500] + '...' if len(content) > 500 else content)
else:
    print('No recent performance reports found. Run comprehensive analysis first.')
"
```

## Usage Examples:

1. **Daily Check**: Use portfolio status + daily market check
2. **Weekly Review**: Run full analysis + rebalancing check  
3. **Monthly Planning**: Generate comprehensive report + risk assessment
4. **Quarterly Action**: Execute rebalancing based on recommendations

Focus on maintaining optimal allocation for the $900 portfolio while following medium risk tolerance guidelines.