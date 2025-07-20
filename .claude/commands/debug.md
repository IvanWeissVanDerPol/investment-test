# Debug Investment Analysis System

Comprehensive debugging workflow for identifying and resolving issues in the investment analysis system.

## Debug Workflow:

### 1. System Health Check
```bash
# Run system monitoring and validation
python .claude\hooks\pre_analysis_hook.py
```

### 2. Configuration Validation
```bash
# Validate configuration integrity
cd config
python -c "
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    print('✅ Configuration JSON is valid')
    
    # Check required fields
    required = ['user_profile', 'target_stocks', 'ai_robotics_etfs', 'alert_thresholds']
    missing = [field for field in required if field not in config]
    
    if missing:
        print(f'❌ Missing fields: {missing}')
    else:
        print('✅ All required configuration fields present')
        
    # Validate portfolio balance
    balance = config.get('user_profile', {}).get('dukascopy_balance', 0)
    if balance != 900:
        print(f'⚠️  Portfolio balance is {balance}, expected 900')
    else:
        print('✅ Portfolio balance correct')
        
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

### 3. Module Import Testing
```bash
# Test all analysis modules can be imported
cd ..
python -c "
import sys
sys.path.append('src')

modules = [
    'investment_system.analysis.quick_analysis',
    'investment_system.analysis.comprehensive_analyzer',
    'investment_system.analysis.news_sentiment_analyzer',
    'investment_system.portfolio.risk_management',
    'investment_system.data.market_data_collector',
    'investment_system.utils.cache_manager'
]

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except Exception as e:
        print(f'❌ {module}: {str(e)[:50]}...')
"
```

### 4. API Connectivity Testing
```bash
# Test external API connections
python -c "
import requests
import time

apis = [
    ('Yahoo Finance', 'https://query1.finance.yahoo.com/v1/finance/search?q=NVDA'),
    ('Alpha Vantage', 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo'),
    ('News API', 'https://newsapi.org/v2/everything?q=NVIDIA&apiKey=demo')
]

for name, url in apis:
    try:
        start_time = time.time()
        response = requests.head(url, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code < 400:
            print(f'✅ {name}: {response.status_code} ({elapsed:.2f}s)')
        else:
            print(f'❌ {name}: HTTP {response.status_code}')
    except Exception as e:
        print(f'❌ {name}: {str(e)[:50]}...')
"
```

### 5. Data Pipeline Testing
```bash
# Test data collection and processing
python -c "
try:
    import yfinance as yf
    
    # Test stock data retrieval
    ticker = yf.Ticker('NVDA')
    info = ticker.info
    hist = ticker.history(period='1d')
    
    if not hist.empty:
        print('✅ Stock data retrieval working')
        print(f'   NVDA current price: ${info.get(\"currentPrice\", \"N/A\")}')
    else:
        print('❌ Stock data retrieval failed')
        
except Exception as e:
    print(f'❌ Data pipeline error: {e}')
"
```

### 6. Cache System Check
```bash
# Verify cache system functionality
python -c "
from pathlib import Path
import json
from datetime import datetime

cache_dir = Path('cache')
if cache_dir.exists():
    cache_files = list(cache_dir.glob('*.json'))
    print(f'Cache files found: {len(cache_files)}')
    
    for cache_file in cache_files[:3]:  # Check first 3
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            print(f'✅ {cache_file.name}: {age_hours:.1f}h old')
        except Exception as e:
            print(f'❌ {cache_file.name}: {str(e)[:30]}...')
else:
    print('⚠️  Cache directory not found')
"
```

### 7. Report Generation Testing
```bash
# Test report generation system
python -c "
from pathlib import Path
import json

reports_dir = Path('reports')
if reports_dir.exists():
    recent_reports = sorted(reports_dir.glob('*.json'), 
                           key=lambda f: f.stat().st_mtime, reverse=True)
    
    if recent_reports:
        latest = recent_reports[0]
        try:
            with open(latest, 'r') as f:
                report = json.load(f)
            
            required_fields = ['generated_at', 'analysis_type', 'recommendations']
            missing = [field for field in required_fields if field not in report]
            
            if missing:
                print(f'❌ Report missing fields: {missing}')
            else:
                print(f'✅ Latest report valid: {latest.name}')
                
        except Exception as e:
            print(f'❌ Report validation error: {e}')
    else:
        print('⚠️  No recent reports found')
else:
    print('❌ Reports directory not found')
"
```

### 8. Performance Diagnostics
```bash
# Check system performance metrics
python -c "
import time
import psutil
import subprocess

print('=== PERFORMANCE DIAGNOSTICS ===')

# CPU and Memory
cpu_percent = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory()
print(f'CPU Usage: {cpu_percent:.1f}%')
print(f'Memory Usage: {memory.percent:.1f}%')
print(f'Available Memory: {memory.available / 1024**3:.1f} GB')

# Test quick analysis speed
print('\\nTesting analysis speed...')
start_time = time.time()
try:
    result = subprocess.run([
        'python', '-c', 
        'from src.investment_system.analysis.quick_analysis import get_stock_analysis; print(\"Test completed\" if get_stock_analysis(\"MSFT\") else \"Test failed\")'
    ], capture_output=True, timeout=60, text=True)
    
    elapsed = time.time() - start_time
    if result.returncode == 0:
        print(f'✅ Quick analysis test: {elapsed:.2f}s')
    else:
        print(f'❌ Quick analysis failed: {result.stderr[:50]}...')
except subprocess.TimeoutExpired:
    print('❌ Quick analysis timeout (>60s)')
except Exception as e:
    print(f'❌ Performance test error: {e}')
"
```

## Debug Report Summary

After running all diagnostics, review:
1. **Configuration Issues**: Any missing or invalid config settings
2. **Module Import Errors**: Python package or dependency issues  
3. **API Connectivity**: Network or authentication problems
4. **Data Pipeline**: Market data retrieval and processing issues
5. **Cache System**: Cache corruption or access problems
6. **Report Generation**: Output format or file access issues
7. **Performance**: Speed or resource utilization concerns

## Common Issues & Solutions

### Configuration Problems
- Verify `config/config.json` syntax and required fields
- Check portfolio balance and risk tolerance settings
- Validate API key configurations

### Import Errors
- Run `pip install -r requirements.txt`
- Check Python path and module structure
- Verify all `__init__.py` files are present

### API Issues
- Test network connectivity
- Verify API rate limits and quotas
- Check for service outages

### Performance Issues
- Clear cache directory if corrupted
- Check available disk space and memory
- Monitor CPU usage during analysis

Use this debug workflow to systematically identify and resolve issues in the investment analysis system.