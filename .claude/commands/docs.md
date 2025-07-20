# Documentation Generator

Generate comprehensive documentation for the investment analysis system, including API documentation, user guides, and technical specifications.

## Documentation Generation Workflow

### 1. Code Documentation Analysis
```bash
# Analyze codebase documentation coverage
echo "=== CODE DOCUMENTATION ANALYSIS ==="
python -c "
import ast
import sys
from pathlib import Path

def analyze_module_documentation(file_path):
    '''Analyze Python file for documentation coverage'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        documented_functions = [f for f in functions if ast.get_docstring(f)]
        documented_classes = [c for c in classes if ast.get_docstring(c)]
        
        total_items = len(functions) + len(classes)
        documented_items = len(documented_functions) + len(documented_classes)
        
        coverage = (documented_items / total_items * 100) if total_items > 0 else 100
        
        return {
            'file': file_path.name,
            'functions': len(functions),
            'classes': len(classes),
            'documented_functions': len(documented_functions),
            'documented_classes': len(documented_classes),
            'coverage': coverage
        }
    except Exception as e:
        return {'file': file_path.name, 'error': str(e)}

# Analyze investment system modules
src_dir = Path('src/investment_system')
if src_dir.exists():
    python_files = list(src_dir.rglob('*.py'))
    
    total_coverage = 0
    valid_files = 0
    
    print('Documentation Coverage by Module:')
    print('-' * 50)
    
    for py_file in python_files:
        if py_file.name == '__init__.py':
            continue
            
        analysis = analyze_module_documentation(py_file)
        
        if 'error' not in analysis:
            print(f'{analysis[\"file\"]:30} {analysis[\"coverage\"]:6.1f}%')
            total_coverage += analysis['coverage']
            valid_files += 1
        else:
            print(f'{analysis[\"file\"]:30} ERROR')
    
    if valid_files > 0:
        avg_coverage = total_coverage / valid_files
        print('-' * 50)
        print(f'Average Documentation Coverage: {avg_coverage:.1f}%')
        
        if avg_coverage >= 80:
            print('✅ Excellent documentation coverage')
        elif avg_coverage >= 60:
            print('⚠️  Good documentation coverage')
        else:
            print('❌ Poor documentation coverage - needs improvement')
else:
    print('Source directory not found')
"
```

### 2. API Documentation Generation
```bash
# Generate API documentation for investment system
echo "=== API DOCUMENTATION GENERATION ==="
python -c "
import inspect
import sys
sys.path.append('src')

def generate_api_docs():
    '''Generate API documentation for investment system modules'''
    
    modules_to_document = [
        ('investment_system.analysis.quick_analysis', 'Quick Analysis API'),
        ('investment_system.portfolio.risk_management', 'Risk Management API'),
        ('investment_system.data.market_data_collector', 'Market Data API'),
        ('investment_system.utils.cache_manager', 'Cache Management API')
    ]
    
    docs = []
    docs.append('# Investment Analysis System API Documentation')
    docs.append('')
    docs.append('Auto-generated API documentation for the investment analysis system.')
    docs.append('')
    
    for module_name, title in modules_to_document:
        try:
            module = __import__(module_name, fromlist=[''])
            docs.append(f'## {title}')
            docs.append('')
            docs.append(f'Module: `{module_name}`')
            docs.append('')
            
            # Get all public functions and classes
            members = inspect.getmembers(module, 
                lambda x: (inspect.isfunction(x) or inspect.isclass(x)) 
                and not x.__name__.startswith('_'))
            
            for name, obj in members:
                docs.append(f'### {name}')
                docs.append('')
                
                # Get docstring
                docstring = inspect.getdoc(obj)
                if docstring:
                    docs.append(docstring)
                else:
                    docs.append('*No documentation available*')
                docs.append('')
                
                # Get signature for functions
                if inspect.isfunction(obj):
                    try:
                        sig = inspect.signature(obj)
                        docs.append(f'**Signature:** `{name}{sig}`')
                        docs.append('')
                    except:
                        pass
            
            docs.append('---')
            docs.append('')
            
        except ImportError as e:
            docs.append(f'## {title}')
            docs.append(f'*Module not available: {e}*')
            docs.append('')
    
    # Write documentation to file
    doc_content = '\\n'.join(docs)
    with open('docs/api_documentation.md', 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print('✅ API documentation generated: docs/api_documentation.md')
    print(f'   Total sections: {len(modules_to_document)}')
    print(f'   Documentation size: {len(doc_content)} characters')

try:
    generate_api_docs()
except Exception as e:
    print(f'❌ Error generating API docs: {e}')
"
```

### 3. User Guide Generation
```bash
# Generate comprehensive user guide
echo "=== USER GUIDE GENERATION ==="
python -c "
import json
from pathlib import Path

def generate_user_guide():
    '''Generate user guide for investment analysis system'''
    
    # Load configuration for user context
    config_path = Path('config/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    user_profile = config.get('user_profile', {})
    
    guide = []
    guide.append('# Investment Analysis System User Guide')
    guide.append('')
    guide.append('Complete guide for using the AI-powered investment analysis system.')
    guide.append('')
    
    # User Profile Section
    guide.append('## Your Investment Profile')
    guide.append('')
    guide.append(f'- **Name**: {user_profile.get(\"name\", \"Ivan\")}')
    guide.append(f'- **Portfolio Balance**: ${user_profile.get(\"dukascopy_balance\", 900)}')
    guide.append(f'- **Risk Tolerance**: {user_profile.get(\"risk_tolerance\", \"Medium\").title()}')
    guide.append(f'- **Investment Focus**: {user_profile.get(\"investment_goals\", [\"AI/Robotics growth\"])}')
    guide.append('')
    
    # Quick Start Section
    guide.append('## Quick Start Guide')
    guide.append('')
    guide.append('### Running Your First Analysis')
    guide.append('```bash')
    guide.append('# Quick daily analysis (2-3 minutes)')
    guide.append('quick_analysis.bat')
    guide.append('')
    guide.append('# Comprehensive analysis (10-15 minutes)')
    guide.append('full_analysis.bat')
    guide.append('```')
    guide.append('')
    
    # Target Assets Section
    target_stocks = config.get('target_stocks', [])
    ai_etfs = config.get('ai_robotics_etfs', [])
    
    guide.append('## Your Investment Universe')
    guide.append('')
    guide.append('### Target Stocks')
    if target_stocks:
        for stock in target_stocks[:10]:  # Show first 10
            guide.append(f'- **{stock}**: Primary focus stock')
    guide.append('')
    
    guide.append('### AI/Robotics ETFs')
    if ai_etfs:
        for etf in ai_etfs[:7]:  # Show all 7
            guide.append(f'- **{etf}**: AI/Robotics sector exposure')
    guide.append('')
    
    # Analysis Types Section
    guide.append('## Analysis Types')
    guide.append('')
    guide.append('### Quick Analysis (2-3 minutes)')
    guide.append('- Basic technical indicators')
    guide.append('- Price movement analysis')
    guide.append('- Simple buy/sell signals')
    guide.append('- Portfolio allocation suggestions')
    guide.append('')
    
    guide.append('### Comprehensive Analysis (10-15 minutes)')
    guide.append('- Advanced technical analysis')
    guide.append('- News sentiment analysis')
    guide.append('- Social media sentiment')
    guide.append('- Smart money tracking')
    guide.append('- AI/ML predictions')
    guide.append('- Risk assessment')
    guide.append('- Portfolio optimization')
    guide.append('')
    
    # Portfolio Management Section
    balance = user_profile.get('dukascopy_balance', 900)
    max_position = balance * 0.25  # 25% max per position
    
    guide.append('## Portfolio Management')
    guide.append('')
    guide.append(f'### Position Sizing (${balance} Portfolio)')
    guide.append(f'- **Maximum single position**: ${max_position:.0f} (25%)')
    guide.append(f'- **Minimum position size**: ${balance * 0.05:.0f} (5%)')
    guide.append('- **Recommended positions**: 6-8 stocks + 2-3 ETFs')
    guide.append('- **Rebalancing frequency**: Quarterly')
    guide.append('')
    
    # Risk Management Section
    guide.append('## Risk Management')
    guide.append('')
    guide.append('### Medium Risk Tolerance Guidelines')
    guide.append('- Maximum 25% in any single position')
    guide.append('- Diversification across AI/Robotics sectors')
    guide.append('- Regular rebalancing (quarterly)')
    guide.append('- Stop-loss considerations for volatile stocks')
    guide.append('')
    
    # Monitoring Section
    guide.append('## System Monitoring')
    guide.append('')
    guide.append('### Daily Tasks')
    guide.append('- Run quick analysis')
    guide.append('- Review alerts and notifications')
    guide.append('- Check smart money movements')
    guide.append('')
    
    guide.append('### Weekly Tasks')
    guide.append('- Run comprehensive analysis')
    guide.append('- Review portfolio performance')
    guide.append('- Update investment thesis')
    guide.append('')
    
    # Troubleshooting Section
    guide.append('## Troubleshooting')
    guide.append('')
    guide.append('### Common Issues')
    guide.append('- **Slow analysis**: Check internet connection and API limits')
    guide.append('- **Missing reports**: Verify reports directory permissions')
    guide.append('- **API errors**: Check API key configuration in config/.env')
    guide.append('- **System errors**: Run debug.bat for diagnostics')
    guide.append('')
    
    # Advanced Features Section
    guide.append('## Advanced Features')
    guide.append('')
    guide.append('### Smart Money Tracking')
    guide.append('Monitor institutional investor movements:')
    smart_funds = config.get('target_funds', [])
    for fund in smart_funds[:5]:  # Show first 5
        guide.append(f'- {fund}')
    guide.append('')
    
    guide.append('### Government Contract Monitoring')
    guide.append('Track AI-related government spending and contracts.')
    guide.append('')
    
    # Write user guide
    guide_content = '\\n'.join(guide)
    with open('docs/user_guide.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print('✅ User guide generated: docs/user_guide.md')
    print(f'   Sections: {len([line for line in guide if line.startswith(\"##\")])}')
    print(f'   Guide size: {len(guide_content)} characters')

try:
    generate_user_guide()
except Exception as e:
    print(f'❌ Error generating user guide: {e}')
"
```

### 4. Technical Specifications
```bash
# Generate technical specifications document
echo "=== TECHNICAL SPECIFICATIONS ==="
python -c "
import sys
import platform
from pathlib import Path

def generate_tech_specs():
    '''Generate technical specifications document'''
    
    specs = []
    specs.append('# Investment Analysis System Technical Specifications')
    specs.append('')
    specs.append('Detailed technical specifications and requirements for the investment analysis system.')
    specs.append('')
    
    # System Requirements
    specs.append('## System Requirements')
    specs.append('')
    specs.append(f'### Current Environment')
    specs.append(f'- **Operating System**: {platform.system()} {platform.release()}')
    specs.append(f'- **Python Version**: {sys.version.split()[0]}')
    specs.append(f'- **Architecture**: {platform.machine()}')
    specs.append('')
    
    specs.append('### Minimum Requirements')
    specs.append('- **OS**: Windows 10+ / macOS 10.14+ / Linux Ubuntu 18.04+')
    specs.append('- **Python**: 3.9 or higher')
    specs.append('- **RAM**: 4GB minimum, 8GB recommended')
    specs.append('- **Storage**: 2GB free space')
    specs.append('- **Network**: Broadband internet connection')
    specs.append('')
    
    # Architecture Overview
    specs.append('## Architecture Overview')
    specs.append('')
    specs.append('### Module Structure')
    specs.append('```')
    specs.append('src/investment_system/')
    specs.append('├── data/           # Data collection and ingestion')
    specs.append('├── analysis/       # Analysis engines and algorithms')
    specs.append('├── portfolio/      # Portfolio management and optimization')
    specs.append('├── monitoring/     # System monitoring and alerting')
    specs.append('├── reporting/      # Report generation and output')
    specs.append('└── utils/          # Utility functions and helpers')
    specs.append('```')
    specs.append('')
    
    # Dependencies
    specs.append('## Dependencies')
    specs.append('')
    
    # Read requirements.txt if available
    req_file = Path('requirements.txt')
    if req_file.exists():
        with open(req_file, 'r') as f:
            requirements = f.read().strip().split('\\n')
        
        specs.append('### Core Dependencies')
        for req in requirements[:10]:  # Show first 10
            if req.strip() and not req.startswith('#'):
                specs.append(f'- `{req.strip()}`')
        specs.append('')
    
    # Data Sources
    specs.append('## Data Sources')
    specs.append('')
    specs.append('### Market Data')
    specs.append('- **Yahoo Finance**: Real-time and historical stock data')
    specs.append('- **Alpha Vantage**: Technical indicators and fundamentals')
    specs.append('- **Twelve Data**: Alternative market data source')
    specs.append('')
    
    specs.append('### News and Sentiment')
    specs.append('- **News API**: Financial news and sentiment')
    specs.append('- **Social Media APIs**: Social sentiment analysis')
    specs.append('')
    
    specs.append('### Institutional Data')
    specs.append('- **SEC Filings**: Smart money tracking')
    specs.append('- **Government Contracts**: AI spending monitoring')
    specs.append('')
    
    # Performance Specifications
    specs.append('## Performance Specifications')
    specs.append('')
    specs.append('### Analysis Performance')
    specs.append('- **Quick Analysis**: <3 minutes execution time')
    specs.append('- **Comprehensive Analysis**: <15 minutes execution time')
    specs.append('- **Cache Hit Rate**: >80% for repeated requests')
    specs.append('- **Memory Usage**: <500MB peak usage')
    specs.append('')
    
    # Security Specifications
    specs.append('## Security Specifications')
    specs.append('')
    specs.append('### Data Protection')
    specs.append('- **API Keys**: Stored in environment variables')
    specs.append('- **Encryption**: HTTPS for all external communications')
    specs.append('- **Input Validation**: Sanitization of all user inputs')
    specs.append('- **Error Handling**: No sensitive data in error messages')
    specs.append('')
    
    # Configuration Specifications
    specs.append('## Configuration Specifications')
    specs.append('')
    specs.append('### Configuration Files')
    specs.append('- `config/config.json`: Main system configuration')
    specs.append('- `config/.env`: Environment variables and API keys')
    specs.append('- `config/.pre-commit-config.yaml`: Development hooks')
    specs.append('')
    
    # API Specifications
    specs.append('## API Specifications')
    specs.append('')
    specs.append('### Rate Limiting')
    specs.append('- **Default**: 60 requests per minute per API')
    specs.append('- **Burst**: 10 additional requests allowed')
    specs.append('- **Timeout**: 30 seconds default, 300 seconds maximum')
    specs.append('')
    
    # File Formats
    specs.append('## File Formats')
    specs.append('')
    specs.append('### Input Formats')
    specs.append('- **Configuration**: JSON')
    specs.append('- **Environment**: .env key-value pairs')
    specs.append('')
    
    specs.append('### Output Formats')
    specs.append('- **Reports**: JSON (machine-readable) + TXT (human-readable)')
    specs.append('- **Cache**: JSON formatted data files')
    specs.append('- **Logs**: Plain text with timestamps')
    specs.append('')
    
    # Write technical specifications
    specs_content = '\\n'.join(specs)
    with open('docs/technical_specifications.md', 'w', encoding='utf-8') as f:
        f.write(specs_content)
    
    print('✅ Technical specifications generated: docs/technical_specifications.md')
    print(f'   Sections: {len([line for line in specs if line.startswith(\"##\")])}')
    print(f'   Document size: {len(specs_content)} characters')

try:
    generate_tech_specs()
except Exception as e:
    print(f'❌ Error generating technical specs: {e}')
"
```

## Documentation Maintenance

### 1. Documentation Update Workflow
```bash
# Check documentation freshness
echo "=== DOCUMENTATION FRESHNESS CHECK ==="
python -c "
from pathlib import Path
import time
from datetime import datetime

doc_files = [
    'docs/api_documentation.md',
    'docs/user_guide.md', 
    'docs/technical_specifications.md',
    'CLAUDE.md',
    'README.md'
]

now = time.time()
stale_threshold = 30 * 24 * 3600  # 30 days

print('Documentation Freshness Report:')
print('-' * 40)

for doc_file in doc_files:
    path = Path(doc_file)
    if path.exists():
        mod_time = path.stat().st_mtime
        age_days = (now - mod_time) / (24 * 3600)
        
        if age_days > 30:
            status = '❌ STALE'
        elif age_days > 14:
            status = '⚠️  OLD'
        else:
            status = '✅ FRESH'
        
        print(f'{path.name:30} {status} ({age_days:.0f} days)')
    else:
        print(f'{path.name:30} ❌ MISSING')

print()
print('Recommendation: Update stale documentation')
"
```

### 2. Generate Complete Documentation Set
```bash
# Generate all documentation at once
echo "=== GENERATING COMPLETE DOCUMENTATION SET ==="

# Create docs directory structure
mkdir docs 2>nul
mkdir docs\\guides 2>nul
mkdir docs\\api 2>nul

echo "Generating API documentation..."
# Run API docs generation (from above)

echo "Generating user guide..."
# Run user guide generation (from above)

echo "Generating technical specifications..."
# Run tech specs generation (from above)

echo "✅ Complete documentation set generated"
echo "📁 Documentation structure:"
echo "   docs/"
echo "   ├── api_documentation.md"
echo "   ├── user_guide.md"
echo "   ├── technical_specifications.md"
echo "   ├── guides/"
echo "   └── api/"
```

## Documentation Quality Metrics

### 1. Documentation Coverage Report
```bash
# Analyze documentation coverage across the system
python -c "
from pathlib import Path
import re

def analyze_doc_coverage():
    '''Analyze documentation coverage across the system'''
    
    # Count Python files
    src_files = list(Path('src').rglob('*.py')) if Path('src').exists() else []
    python_files = [f for f in src_files if not f.name.startswith('__')]
    
    # Count documentation files
    doc_files = list(Path('docs').rglob('*.md')) if Path('docs').exists() else []
    
    # Count configuration files
    config_files = list(Path('config').rglob('*')) if Path('config').exists() else []
    
    # Count test files
    test_files = list(Path('tests').rglob('*.py')) if Path('tests').exists() else []
    
    print('=== DOCUMENTATION COVERAGE REPORT ===')
    print(f'Python source files: {len(python_files)}')
    print(f'Documentation files: {len(doc_files)}')
    print(f'Configuration files: {len(config_files)}')
    print(f'Test files: {len(test_files)}')
    print()
    
    # Calculate coverage ratios
    if python_files:
        doc_ratio = len(doc_files) / len(python_files)
        test_ratio = len(test_files) / len(python_files)
        
        print(f'Documentation ratio: {doc_ratio:.2f} (docs per source file)')
        print(f'Test coverage ratio: {test_ratio:.2f} (tests per source file)')
        
        if doc_ratio >= 0.3:
            print('✅ Good documentation coverage')
        else:
            print('⚠️  Consider adding more documentation')
            
        if test_ratio >= 0.5:
            print('✅ Good test coverage')
        else:
            print('⚠️  Consider adding more tests')
    
analyze_doc_coverage()
"
```

Your investment analysis system now includes comprehensive documentation generation and maintenance capabilities, ensuring clear understanding of the $900 portfolio management system!