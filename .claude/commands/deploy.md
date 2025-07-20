# Deploy Investment Analysis System

Comprehensive deployment workflow for setting up the investment analysis system in production or new environments.

## Pre-Deployment Checklist

### 1. Environment Preparation
```bash
# Verify Python version
python --version  # Should be 3.9+

# Check available disk space
dir C:\ | find "bytes free"  # Should have >2GB free

# Verify Git repository status
git status
git log --oneline -5
```

### 2. Configuration Security Audit
```bash
# Check for exposed secrets
findstr /R /S "sk-.*" src\
findstr /R /S "API_KEY.*=" src\
findstr /R /S "password.*=" config\

# Validate .env.example doesn't contain real keys
type config\.env.example | findstr /V "your_.*_here"
```

## Deployment Steps

### 1. Fresh Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black isort flake8 mypy pre-commit

# Setup pre-commit hooks
pre-commit install --config config\.pre-commit-config.yaml
```

### 2. Environment Configuration
```bash
# Create production environment file
copy config\.env.example config\.env
echo "Please configure config\.env with production API keys and settings"

# Validate configuration
python -c "
import json
with open('config/config.json', 'r') as f:
    config = json.load(f)
print('Portfolio Balance:', config['user_profile']['dukascopy_balance'])
print('Risk Tolerance:', config['user_profile']['risk_tolerance'])
print('Target Stocks:', len(config['target_stocks']))
print('AI/Robotics ETFs:', len(config['ai_robotics_etfs']))
"
```

### 3. System Validation
```bash
# Run comprehensive system check
python .claude\hooks\pre_analysis_hook.py

# Test all analysis modules
python -c "
modules = [
    'src.investment_system.analysis.quick_analysis',
    'src.investment_system.analysis.comprehensive_analyzer',
    'src.investment_system.portfolio.risk_management',
    'src.investment_system.monitoring.system_monitor'
]

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module.split(\".\")[-1]}')
    except Exception as e:
        print(f'❌ {module.split(\".\")[-1]}: {e}')
"
```

### 4. Directory Structure Creation
```bash
# Ensure all required directories exist
mkdir reports 2>nul
mkdir cache 2>nul
mkdir logs 2>nul

# Set appropriate permissions
echo "Directories created successfully"
```

### 5. Initial Data Population
```bash
# Run initial system health check
python src\investment_system\monitoring\system_monitor.py --one-shot

# Populate initial cache with target stocks
python -c "
from src.investment_system.data.market_data_collector import MarketDataCollector
import json

with open('config/config.json', 'r') as f:
    config = json.load(f)

collector = MarketDataCollector()
target_stocks = config['target_stocks'][:3]  # Test with first 3

for symbol in target_stocks:
    try:
        data = collector.get_stock_data(symbol)
        print(f'✅ Cached data for {symbol}')
    except Exception as e:
        print(f'❌ Failed to cache {symbol}: {e}')
"
```

### 6. Monitoring Setup
```bash
# Test alert system
python -c "
from src.investment_system.monitoring.alert_system import AlertSystem
alert_system = AlertSystem()
print('✅ Alert system initialized')
"

# Configure Windows Task Scheduler for monitoring
echo "Consider setting up Windows Task Scheduler for:"
echo "  - Daily analysis: scripts\run_daily_analysis.bat"
echo "  - System monitoring: scripts\run_system_monitor.bat"
```

## Production Configuration

### 1. API Keys Configuration
```bash
# Remind user to configure production API keys
echo "=== PRODUCTION API KEYS REQUIRED ==="
echo "Edit config\.env with:"
echo "  ALPHA_VANTAGE_API_KEY=your_real_key"
echo "  NEWSAPI_API_KEY=your_real_key"
echo "  FINNHUB_API_KEY=your_real_key"
echo "  TWELVEDATA_API_KEY=your_real_key"
```

### 2. Email Notifications Setup
```bash
# Configure email alerts
echo "=== EMAIL NOTIFICATIONS SETUP ==="
echo "Edit config\.env with:"
echo "  EMAIL_ENABLED=true"
echo "  EMAIL_USERNAME=your_email@gmail.com"
echo "  EMAIL_PASSWORD=your_app_password"
echo "  EMAIL_RECIPIENT=your_email@gmail.com"
```

### 3. Performance Optimization
```bash
# Set production performance settings
python -c "
import json

# Load config
with open('config/config.json', 'r') as f:
    config = json.load(f)

# Optimize for production
config['cache_settings'] = {
    'enabled': True,
    'default_expiry_hours': 6,
    'max_cache_size_mb': 100
}

config['performance_settings'] = {
    'max_concurrent_requests': 5,
    'request_timeout_seconds': 30,
    'retry_attempts': 3
}

# Save optimized config
with open('config/config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('✅ Production performance settings applied')
"
```

## Post-Deployment Testing

### 1. End-to-End Analysis Test
```bash
# Run complete analysis workflow
echo "Running end-to-end test..."
python src\investment_system\analysis\quick_analysis.py

# Verify reports generation
dir reports\*.json | find /c ".json"
dir reports\*.txt | find /c ".txt"
```

### 2. Monitoring System Test
```bash
# Test monitoring system
timeout 30 python src\investment_system\monitoring\system_monitor.py

echo "✅ Monitoring system test completed"
```

### 3. Portfolio Analysis Test
```bash
# Test portfolio analysis with current balance
python -c "
from src.investment_system.portfolio.risk_management import RiskManager
risk_manager = RiskManager()

# Test with $900 portfolio
portfolio_value = 900
max_position = portfolio_value * 0.25  # 25% max per position
print(f'Portfolio: ${portfolio_value}')
print(f'Max single position: ${max_position}')
print('✅ Portfolio analysis test passed')
"
```

## Deployment Verification

### Final Checklist
- [ ] All Python dependencies installed
- [ ] Configuration files properly set
- [ ] API keys configured (production)
- [ ] Email notifications setup
- [ ] Directory structure created
- [ ] Pre-commit hooks installed
- [ ] System monitoring functional
- [ ] Analysis modules working
- [ ] Reports generating properly
- [ ] Cache system operational

### Success Criteria
1. **Quick Analysis**: Completes in under 3 minutes
2. **Comprehensive Analysis**: Completes in under 15 minutes
3. **System Monitor**: Runs without errors
4. **Reports Generated**: JSON and text formats created
5. **API Connectivity**: All external APIs accessible
6. **Email Alerts**: Notifications working (if configured)

## Rollback Plan

If deployment fails:
1. Restore previous configuration files
2. Check error logs in `reports/` directory
3. Run debug workflow: `/debug`
4. Verify Python environment: `pip list`
5. Check disk space and permissions

## Maintenance Schedule

After successful deployment:
- **Daily**: Monitor system health logs
- **Weekly**: Review analysis accuracy and performance
- **Monthly**: Update API keys and configuration
- **Quarterly**: Portfolio rebalancing (Oct 1, 2025)

Your investment analysis system is now deployed and ready for $900 portfolio management with AI/Robotics focus!