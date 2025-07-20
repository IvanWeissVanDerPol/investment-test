# Clean Investment Analysis Code

Fix all Python code formatting, import organization, and linting issues in the investment analysis system.

## What this command does:

1. **Code Formatting**: Apply Black formatting to all Python files in `tools/`
2. **Import Organization**: Sort imports using isort 
3. **Linting**: Fix flake8 issues where possible
4. **Type Checking**: Identify and suggest mypy type hint improvements

## Execution Steps:

### 1. Format Python Files
```bash
cd tools
python -m black *.py
```

### 2. Organize Imports
```bash
cd tools  
python -m isort *.py
```

### 3. Check Linting Issues
```bash
cd tools
python -m flake8 *.py --max-line-length=88 --ignore=E203,W503
```

### 4. Type Checking Analysis
```bash
cd tools
python -m mypy *.py --ignore-missing-imports
```

## Investment Analysis Specific Rules:

- **Configuration Validation**: Ensure `config.json` loads properly in all modules
- **API Key Security**: Never expose API keys in formatted output
- **Report Generation**: Maintain JSON structure integrity after formatting
- **Module Dependencies**: Preserve import chains between analysis modules

## Files to Focus On:
- `quick_analysis.py` - Core daily analysis
- `comprehensive_analyzer.py` - Master analysis orchestrator  
- `news_sentiment_analyzer.py` - News analysis module
- `social_sentiment_analyzer.py` - Social sentiment tracking
- `risk_management.py` - Portfolio risk calculations
- `config.json` - Configuration validation

## Expected Outcome:
Clean, consistently formatted Python codebase with organized imports and minimal linting issues, while preserving the investment analysis functionality.