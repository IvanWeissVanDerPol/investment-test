# Interactive Brokers Integration

Connect to Interactive Brokers to access real-time account balance, positions, and portfolio data for accurate investment analysis.

## Setup and Connection

### 1. Install Required Dependencies
```bash
# Install Interactive Brokers Python library
pip install ib_insync

# Verify installation
python -c "import ib_insync; print('✅ ib_insync installed successfully')"
```

### 2. Configure Interactive Brokers API Access

#### Option A: TWS (Trader Workstation)
1. **Download and Install TWS**: Get from Interactive Brokers website
2. **Enable API Access**:
   - Login to TWS
   - Go to `File > Global Configuration > API > Settings`
   - Check "Enable ActiveX and Socket Clients"
   - Set Socket Port: `7497` (paper) or `7496` (live)
   - Check "Download open orders on connection"
   - Click "OK" and restart TWS

#### Option B: IB Gateway (Lighter Alternative)
1. **Download IB Gateway**: Standalone API application
2. **Configure API Settings**:
   - Socket Port: `4001` (paper) or `4000` (live)
   - Enable API connections
   - Set trusted IP addresses (127.0.0.1 for local)

### 3. Test Connection
```bash
# Test TWS connection
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager
manager = LivePortfolioManager(connection_type='tws')
if manager.connect():
    print('✅ TWS connection successful')
    manager.disconnect()
else:
    print('❌ TWS connection failed')
"

# Test Gateway connection
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager
manager = LivePortfolioManager(connection_type='gateway')
if manager.connect():
    print('✅ Gateway connection successful')
    manager.disconnect()
else:
    print('❌ Gateway connection failed')
"
```

## Live Portfolio Access

### 1. Get Current Account Balance
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

manager = LivePortfolioManager()
if manager.connect():
    balance = manager.get_account_balance()
    
    print('=== ACCOUNT BALANCE ===')
    print(f'Net Liquidation: ${balance.get(\"net_liquidation\", 0):,.2f}')
    print(f'Buying Power: ${balance.get(\"buying_power\", 0):,.2f}')
    print(f'Total Cash: ${balance.get(\"total_cash\", 0):,.2f}')
    print(f'Available Funds: ${balance.get(\"available_funds\", 0):,.2f}')
    
    manager.disconnect()
else:
    print('❌ Failed to connect to Interactive Brokers')
"
```

### 2. Get Current Positions
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

manager = LivePortfolioManager()
if manager.connect():
    positions = manager.get_positions()
    
    print('=== CURRENT POSITIONS ===')
    print(f'Total Positions: {len(positions)}')
    print()
    
    for pos in positions:
        symbol = pos.get('symbol', '')
        position = pos.get('position', 0)
        market_value = pos.get('market_value', 0)
        unrealized_pnl = pos.get('unrealized_pnl', 0)
        
        print(f'{symbol:8} | {position:8.0f} | ${market_value:10,.2f} | ${unrealized_pnl:8,.2f}')
    
    manager.disconnect()
else:
    print('❌ Failed to connect to Interactive Brokers')
"
```

### 3. Get Portfolio Summary for Analysis
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

manager = LivePortfolioManager()
if manager.connect():
    summary = manager.get_portfolio_summary_for_analysis()
    
    if summary:
        account = summary['account_info']
        metrics = summary['portfolio_metrics']
        ai_focus = summary['ai_robotics_focus']
        risk = summary['risk_assessment']
        
        print('=== PORTFOLIO ANALYSIS SUMMARY ===')
        print(f'Account Balance: ${account[\"balance\"]:,.2f}')
        print(f'Buying Power: ${account[\"buying_power\"]:,.2f}')
        print()
        print(f'Total Positions: {metrics[\"total_positions\"]}')
        print(f'Market Value: ${metrics[\"market_value\"]:,.2f}')
        print(f'Unrealized P&L: ${metrics[\"unrealized_pnl\"]:,.2f}')
        print()
        print(f'AI/Robotics Allocation: {ai_focus[\"current_allocation_pct\"]:.1f}%')
        print(f'Target AI Allocation: {ai_focus[\"target_allocation_pct\"]}%')
        print(f'AI Positions Count: {ai_focus[\"ai_positions_count\"]}')
        print()
        print(f'Concentration Risk: {risk[\"concentration_risk\"]:.1f}%')
        print(f'Cash Percentage: {risk[\"cash_percentage\"]:.1f}%')
    
    manager.disconnect()
else:
    print('❌ Failed to connect to Interactive Brokers')
"
```

## Synchronization with Analysis System

### 1. Sync Live Data with Configuration
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

manager = LivePortfolioManager()
if manager.connect():
    if manager.sync_with_analysis_system():
        print('✅ Live portfolio data synced with analysis system')
        print('   Updated config/config.json with current balance and positions')
        print('   Analysis system will now use live data for recommendations')
    else:
        print('❌ Failed to sync portfolio data')
    
    manager.disconnect()
else:
    print('❌ Failed to connect to Interactive Brokers')
"
```

### 2. Check Rebalancing Needs
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

manager = LivePortfolioManager()
if manager.connect():
    rebalancing = manager.check_rebalancing_needs()
    
    print('=== REBALANCING ANALYSIS ===')
    if rebalancing.get('needs_rebalancing'):
        print('⚠️  Portfolio rebalancing recommended')
        print()
        print('Recommendations:')
        for rec in rebalancing.get('recommendations', []):
            print(f'  • {rec}')
        
        print()
        print('Risk Warnings:')
        for warning in rebalancing.get('risk_warnings', []):
            print(f'  ⚠️  {warning}')
    else:
        print('✅ Portfolio is well-balanced')
        print('   No immediate rebalancing needed')
    
    manager.disconnect()
else:
    print('❌ Failed to connect to Interactive Brokers')
"
```

## Integration with Analysis Workflow

### 1. Update Quick Analysis to Use Live Data
The live portfolio data will automatically be used when available:

```bash
# Run analysis with live portfolio data
python -m src.investment_system.analysis.quick_analysis
```

### 2. Comprehensive Analysis with Live Portfolio
```bash
# Run comprehensive analysis including live portfolio assessment
python -m src.investment_system.analysis.comprehensive_analyzer
```

### 3. Automated Sync Schedule
Set up automatic synchronization:

```bash
# Add to Windows Task Scheduler or run manually
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager
import schedule
import time

def sync_portfolio():
    manager = LivePortfolioManager()
    if manager.connect():
        manager.sync_with_analysis_system()
        manager.disconnect()
        print(f'Portfolio synced at {time.strftime(\"%H:%M:%S\")}')

# Sync every 15 minutes during market hours
schedule.every(15).minutes.do(sync_portfolio)

print('🔄 Starting automated portfolio sync...')
while True:
    schedule.run_pending()
    time.sleep(60)
"
```

## Security and Configuration

### 1. API Security Settings
```bash
# Verify secure API configuration
python -c "
import json
from pathlib import Path

config_path = Path('config/config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

ibkr_config = config.get('interactive_brokers', {})

print('=== INTERACTIVE BROKERS CONFIGURATION ===')
print(f'Enabled: {ibkr_config.get(\"enabled\", False)}')
print(f'Connection Type: {ibkr_config.get(\"connection_type\", \"auto\")}')
print(f'Host: {ibkr_config.get(\"host\", \"127.0.0.1\")}')
print(f'TWS Port: {ibkr_config.get(\"tws_port\", 7497)}')
print(f'Gateway Port: {ibkr_config.get(\"gateway_port\", 4001)}')
print(f'Auto Sync: {ibkr_config.get(\"auto_sync\", True)}')
print(f'Sync Interval: {ibkr_config.get(\"sync_interval_minutes\", 15)} minutes')
"
```

### 2. Troubleshooting Connection Issues

#### Common Issues and Solutions:

**"Connection Refused"**:
- Ensure TWS or IB Gateway is running
- Check API settings are enabled
- Verify correct port numbers
- Check firewall settings

**"Authentication Failed"**:
- Login to TWS/Gateway manually first
- Check trusted IP addresses include 127.0.0.1
- Verify API permissions in account settings

**"No Data Returned"**:
- Ensure account has positions/balance
- Check if market is open for real-time data
- Verify API permissions for account data

### 3. Connection Diagnostics
```bash
python -c "
from src.investment_system.portfolio.live_portfolio_manager import LivePortfolioManager

print('=== CONNECTION DIAGNOSTICS ===')

# Test auto connection
manager = LivePortfolioManager(connection_type='auto')
print(f'Auto connection: {\"✅\" if manager.connect() else \"❌\"}')
if manager.is_connected():
    manager.disconnect()

# Test TWS connection
try:
    manager_tws = LivePortfolioManager(connection_type='tws')
    print(f'TWS connection: {\"✅\" if manager_tws.connect() else \"❌\"}')
    if manager_tws.is_connected():
        manager_tws.disconnect()
except Exception as e:
    print(f'TWS connection: ❌ ({str(e)[:50]}...)')

# Test Gateway connection
try:
    manager_gw = LivePortfolioManager(connection_type='gateway')
    print(f'Gateway connection: {\"✅\" if manager_gw.connect() else \"❌\"}')
    if manager_gw.is_connected():
        manager_gw.disconnect()
except Exception as e:
    print(f'Gateway connection: ❌ ({str(e)[:50]}...)')
"
```

## Benefits of Live Integration

### Real-Time Analysis
- **Accurate Balance**: Use actual account balance instead of estimated $900
- **Current Positions**: Analyze actual holdings vs target allocations
- **Live P&L**: Include unrealized gains/losses in analysis
- **Real-Time Risk**: Calculate actual concentration and diversification

### Enhanced Decision Making
- **Precise Rebalancing**: Know exactly what to buy/sell
- **Available Funds**: See actual buying power for new positions
- **Position Sizing**: Calculate optimal sizes based on actual balance
- **Tax Considerations**: Factor in existing positions for tax efficiency

### Automated Monitoring
- **Portfolio Drift**: Alert when allocations deviate from targets
- **Risk Monitoring**: Track concentration and diversification in real-time
- **Performance Tracking**: Monitor actual vs expected returns
- **Compliance**: Ensure positions stay within risk tolerance limits

Your investment analysis system now has direct access to your Interactive Brokers account for real-time portfolio management and analysis!