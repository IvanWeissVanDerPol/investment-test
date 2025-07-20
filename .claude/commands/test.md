# Test Investment Analysis System

Comprehensive testing strategy for the investment analysis system ensuring reliability and accuracy of financial analysis and recommendations.

## Testing Strategy:

### 1. Unit Testing
Test individual functions and methods in isolation:

```bash
# Run all tests
cd tools && python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_quick_analysis.py -v

# Test with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### 2. Integration Testing
Test module interactions and data flow:

```bash
# Test full analysis pipeline
python -m pytest tests/test_integration.py -v

# Test API integrations
python -m pytest tests/test_api_integration.py -v
```

### 3. Investment Logic Testing
Validate financial calculations and investment algorithms:

```bash
# Test portfolio calculations
python -m pytest tests/test_portfolio_logic.py -v

# Test risk management
python -m pytest tests/test_risk_calculations.py -v
```

## Test Categories:

### Core Analysis Tests
- **Signal Generation**: Validate buy/sell signal accuracy
- **Technical Indicators**: Test moving averages, RSI, MACD calculations
- **Portfolio Allocation**: Verify $900 portfolio distribution logic
- **Risk Metrics**: Test risk tolerance and position sizing

### Data Processing Tests
- **Market Data Validation**: Test yfinance data parsing
- **News Sentiment**: Validate sentiment scoring algorithms
- **Social Media Analysis**: Test social sentiment aggregation
- **Cache Management**: Verify cache hit/miss rates

### Configuration Tests
- **Config Loading**: Test `config.json` parsing and validation
- **API Key Management**: Verify secure API key handling
- **Asset Lists**: Validate target stocks and ETFs loading
- **Threshold Settings**: Test alert and confidence thresholds

### Report Generation Tests
- **JSON Output**: Validate report data structure integrity
- **Text Formatting**: Test human-readable report generation
- **File Operations**: Verify report saving and organization
- **Data Consistency**: Test cross-format data consistency

## Investment-Specific Test Scenarios:

### Market Condition Tests
- **Bull Market**: Test analysis behavior in rising markets
- **Bear Market**: Validate defensive positioning logic
- **High Volatility**: Test risk management in volatile conditions
- **Low Volume**: Verify analysis with limited market activity

### Portfolio Scenarios
- **Small Account ($900)**: Test fractional share logic
- **Risk Tolerance**: Validate medium risk allocation
- **Sector Focus**: Test AI/Robotics concentration limits
- **Rebalancing**: Test quarterly rebalancing triggers

### Error Handling Tests
- **API Failures**: Test graceful degradation when APIs are down
- **Invalid Data**: Verify handling of corrupted market data
- **Network Issues**: Test timeout and retry mechanisms
- **Configuration Errors**: Validate error handling for invalid configs

## Performance Tests:
```bash
# Benchmark quick analysis speed
python -c "import time; from quick_analysis import main; start=time.time(); main(); print(f'Execution time: {time.time()-start:.2f}s')"

# Memory usage profiling
python -m memory_profiler tools/comprehensive_analyzer.py
```

## Test Data Management:
- **Mock Market Data**: Use consistent test datasets
- **Historical Scenarios**: Test against known market events
- **Edge Cases**: Test with extreme market conditions
- **Configuration Variants**: Test different user profiles

## Continuous Testing:
```bash
# Pre-commit testing
python -m pytest tests/test_critical.py --maxfail=1

# Daily validation
python tools/test_analysis_accuracy.py

# Weekly regression testing
python -m pytest tests/ --cov=. --cov-fail-under=80
```

## Success Criteria:
- 90%+ test coverage across all modules
- All investment calculations validated against known results
- Error handling covers all identified failure modes
- Performance benchmarks met for quick and comprehensive analysis
- Mock trading scenarios produce expected portfolio outcomes

Ensure all tests pass before deploying changes to the live investment analysis system.