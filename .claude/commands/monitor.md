# Investment System Monitoring

Real-time monitoring and alerting commands for the investment analysis system.

## System Health Monitoring:

### Analysis System Status
Check if all analysis modules are functioning properly:

```bash
cd tools
python -c "
import sys
from pathlib import Path

print('=== INVESTMENT ANALYSIS SYSTEM STATUS ===')
print()

# Check core modules
modules = [
    'quick_analysis.py',
    'comprehensive_analyzer.py', 
    'news_sentiment_analyzer.py',
    'social_sentiment_analyzer.py',
    'risk_management.py',
    'cache_manager.py'
]

for module in modules:
    if Path(module).exists():
        try:
            # Try importing the module
            module_name = module.replace('.py', '')
            __import__(module_name)
            print(f'✅ {module}: Ready')
        except Exception as e:
            print(f'❌ {module}: Error - {str(e)[:50]}...')
    else:
        print(f'❌ {module}: File not found')

print()

# Check configuration
if Path('config.json').exists():
    print('✅ Configuration: Available')
else:
    print('❌ Configuration: Missing config.json')

# Check reports directory
reports_dir = Path('../reports')
if reports_dir.exists():
    recent_reports = list(reports_dir.glob('*.json'))[-5:]  # Last 5 reports
    print(f'✅ Reports: {len(recent_reports)} recent reports found')
else:
    print('❌ Reports: Directory not found')
"
```

### API Connectivity Check
Test connectivity to financial data APIs:

```bash
cd tools
python -c "
import requests
import json
from datetime import datetime

print('=== API CONNECTIVITY STATUS ===')
print(f'Check time: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print()

# Test APIs
apis = [
    ('Yahoo Finance', 'https://query1.finance.yahoo.com/v1/finance/search?q=NVDA'),
    ('Alpha Vantage', 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo'),
    ('News API', 'https://newsapi.org/v2/everything?q=NVIDIA&apiKey=demo')
]

for name, url in apis:
    try:
        response = requests.head(url, timeout=10)
        if response.status_code < 400:
            print(f'✅ {name}: Connected ({response.status_code})')
        else:
            print(f'⚠️  {name}: HTTP {response.status_code}')
    except requests.RequestException as e:
        print(f'❌ {name}: Connection failed - {str(e)[:50]}...')
"
```

### Cache Performance Monitor
Check cache hit rates and performance:

```bash
cd tools
python -c "
from pathlib import Path
import json
from datetime import datetime, timedelta

print('=== CACHE PERFORMANCE MONITOR ===')
print()

cache_dir = Path('../cache')
if cache_dir.exists():
    cache_files = list(cache_dir.glob('*.json'))
    
    # Check cache freshness
    now = datetime.now()
    fresh_count = 0
    stale_count = 0
    
    for cache_file in cache_files:
        mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (now - mod_time).total_seconds() / 3600
        
        if age_hours < 24:  # Fresh if less than 24 hours
            fresh_count += 1
        else:
            stale_count += 1
    
    print(f'Total cache files: {len(cache_files)}')
    print(f'Fresh cache files: {fresh_count} (< 24h)')
    print(f'Stale cache files: {stale_count} (> 24h)')
    
    if cache_files:
        total_size = sum(f.stat().st_size for f in cache_files)
        print(f'Total cache size: {total_size / 1024:.1f} KB')
    
    # Cache efficiency
    if fresh_count > 0:
        efficiency = (fresh_count / len(cache_files)) * 100
        print(f'Cache efficiency: {efficiency:.1f}%')
else:
    print('❌ Cache directory not found')
"
```

## Market Monitoring:

### Real-time Price Alerts
Monitor target stocks for significant price movements:

```bash
cd tools
python -c "
import yfinance as yf
import json
from datetime import datetime

with open('config.json', 'r') as f:
    config = json.load(f)

print('=== REAL-TIME PRICE ALERTS ===')
print(f'Check time: {datetime.now().strftime(\"%H:%M:%S\")}')
print()

# Alert thresholds
price_threshold = config['alert_thresholds']['price_movement_alert']  # 5%
volume_threshold = config['alert_thresholds']['volume_spike_threshold']  # 2x

# Check top holdings
top_stocks = config['target_stocks'][:5]

for symbol in top_stocks:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='2d')
        
        if len(hist) >= 2:
            current_price = hist['Close'][-1]
            prev_price = hist['Close'][-2]
            current_volume = hist['Volume'][-1]
            avg_volume = hist['Volume'][:-1].mean()
            
            price_change = ((current_price / prev_price) - 1) * 100
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price alerts
            if abs(price_change) >= (price_threshold * 100):
                alert_type = '🔴' if price_change < 0 else '🟢'
                print(f'{alert_type} {symbol}: {price_change:+.2f}% price movement')
            
            # Volume alerts  
            if volume_ratio >= volume_threshold:
                print(f'📈 {symbol}: {volume_ratio:.1f}x volume spike')
                
    except Exception as e:
        print(f'❌ {symbol}: Data error - {str(e)[:30]}...')
"
```

### News Sentiment Monitor
Track sentiment changes in financial news:

```bash
cd tools
python news_sentiment_analyzer.py --monitor --stocks="NVDA,MSFT,TSLA" --threshold=0.7
```

### Smart Money Activity
Monitor institutional investor activity:

```bash
cd tools
python smart_money_tracker.py --realtime --threshold=1000000
```

## Performance Monitoring:

### Analysis Execution Times
Track performance of analysis modules:

```bash
cd tools
python -c "
import time
import subprocess
from datetime import datetime

print('=== ANALYSIS PERFORMANCE MONITOR ===')
print()

# Time quick analysis
print('Testing Quick Analysis...')
start_time = time.time()
try:
    result = subprocess.run(['python', 'quick_analysis.py'], 
                          capture_output=True, timeout=300)
    execution_time = time.time() - start_time
    
    if result.returncode == 0:
        print(f'✅ Quick Analysis: {execution_time:.1f} seconds')
    else:
        print(f'❌ Quick Analysis: Failed ({execution_time:.1f}s)')
except subprocess.TimeoutExpired:
    print('❌ Quick Analysis: Timeout (>5 minutes)')
except Exception as e:
    print(f'❌ Quick Analysis: Error - {e}')

# Check system resources
print()
print('System Resources:')
try:
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f'CPU Usage: {cpu_percent:.1f}%')
    print(f'Memory Usage: {memory.percent:.1f}%')
    print(f'Available Memory: {memory.available / 1024**3:.1f} GB')
except ImportError:
    print('Install psutil for system resource monitoring')
"
```

### Report Generation Status
Monitor report generation and file sizes:

```bash
cd tools
python -c "
from pathlib import Path
from datetime import datetime, timedelta

print('=== REPORT GENERATION STATUS ===')
print()

reports_dir = Path('../reports')
if reports_dir.exists():
    # Find reports from last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent_reports = []
    
    for report_file in reports_dir.glob('*'):
        mod_time = datetime.fromtimestamp(report_file.stat().st_mtime)
        if mod_time > cutoff:
            recent_reports.append((report_file, mod_time))
    
    recent_reports.sort(key=lambda x: x[1], reverse=True)
    
    print(f'Reports generated in last 24h: {len(recent_reports)}')
    print()
    
    for report_file, mod_time in recent_reports[:5]:  # Show last 5
        size_kb = report_file.stat().st_size / 1024
        print(f'{mod_time.strftime(\"%H:%M\")} - {report_file.name} ({size_kb:.1f} KB)')
        
    # Check for missing expected reports
    expected_daily = datetime.now().replace(hour=8, minute=0, second=0)
    if datetime.now().hour > 8:  # After 8 AM
        daily_reports = [r for r in recent_reports if 'daily' in r[0].name.lower()]
        if not daily_reports:
            print()
            print('⚠️  No daily reports found since 8:00 AM')
else:
    print('❌ Reports directory not found')
"
```

## Alert Configuration:

### Set Price Alerts
Configure custom price movement alerts:

```bash
cd tools
python -c "
import json

# Load current config
with open('config.json', 'r') as f:
    config = json.load(f)

print('=== CURRENT ALERT SETTINGS ===')
alerts = config['alert_thresholds']

for key, value in alerts.items():
    if 'price' in key or 'movement' in key:
        print(f'{key}: {value*100:.1f}%')
    elif 'threshold' in key:
        print(f'{key}: {value}x')
    else:
        print(f'{key}: {value}')

print()
print('To modify alerts, edit tools/config.json')
print('Recommended settings for $900 portfolio:')
print('- price_movement_alert: 0.05 (5%)')
print('- volume_spike_threshold: 2.0 (2x normal)')
print('- strong_buy_confidence: 0.8 (80%)')
"
```

### Notification Status
Check email notification configuration:

```bash
cd tools
python -c "
import json

with open('config.json', 'r') as f:
    config = json.load(f)

email_settings = config.get('email_settings', {})

print('=== NOTIFICATION STATUS ===')
print(f'Email alerts: {\"Enabled\" if email_settings.get(\"enabled\") else \"Disabled\"}')

if email_settings.get('enabled'):
    print(f'SMTP Server: {email_settings.get(\"smtp_server\")}')
    print(f'Recipient: {email_settings.get(\"recipient\")}')
    
    # Test notification
    print()
    print('To test notifications, run:')
    print('python ../claude/hooks/post_analysis_hook.py')
else:
    print()
    print('To enable notifications:')
    print('1. Set email_settings.enabled = true in config.json')
    print('2. Configure SMTP settings')
    print('3. Set up app password for Gmail')
"
```

## Automated Monitoring:

Set up continuous monitoring with:

```bash
# Run every 15 minutes during market hours
# Add to Windows Task Scheduler or use Python scheduler
cd tools && python monitor_system.py --interval=15m
```

Monitor key metrics:
- Analysis execution times
- API response times  
- Cache hit rates
- Report generation success
- Price movement alerts
- Volume spike detection

Focus on maintaining system reliability for consistent investment decision support.