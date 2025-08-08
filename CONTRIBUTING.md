# Contributing to InvestmentAI

Thank you for your interest in contributing to the InvestmentAI Enhanced System! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/InvestmentAI.git
   cd InvestmentAI
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```
4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## 📋 Development Guidelines

### Code Style
- **Python**: Follow PEP 8 and use Black for formatting
- **Line Length**: 88 characters maximum
- **Imports**: Use isort for import organization
- **Type Hints**: Required for all public functions

### Testing
- **Unit Tests**: Place in `tests/unit/`
- **Integration Tests**: Place in `tests/integration/`  
- **Coverage**: Maintain >75% test coverage
- **Naming**: Use descriptive test function names

### Documentation
- **Docstrings**: Required for all public functions and classes
- **README**: Update for significant changes
- **CHANGELOG**: Document all changes

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v   # Integration tests only

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

## 📊 Investment System Guidelines

### Mathematical Accuracy
- All investment calculations must be mathematically sound
- Include confidence intervals and uncertainty measures
- Validate against historical data where possible

### Risk Management
- Conservative position sizing (default 50% Kelly multiplier)
- Multiple validation layers for trading decisions
- Clear risk warnings in all recommendations

### Data Quality
- Validate all market data sources
- Handle missing or corrupted data gracefully
- Cache data appropriately to avoid rate limits

### Ethics and ESG
- Maintain ethical investment screening
- Prioritize sustainable and responsible investments
- Avoid controversial companies as configured

## 🏗️ Project Structure

```
InvestmentAI/
├── core/                       # Core Python package
│   └── investment_system/      # Main system modules
├── config/                     # Configuration files
├── docs/                       # Documentation (8 sections)
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── web/                        # Web dashboard
├── mcp/                        # MCP server implementations
├── scripts/                    # Automation scripts
└── deploy/                     # Deployment configurations
```

## 🔧 Adding New Features

### 1. Analysis Modules
```python
# Example: new analysis module
from core.investment_system.analysis import BaseAnalyzer

class NewAnalyzer(BaseAnalyzer):
    def analyze(self, symbol: str) -> AnalysisResult:
        # Implementation here
        pass
```

### 2. Portfolio Strategies
```python
# Example: new portfolio strategy  
from core.investment_system.portfolio import BaseStrategy

class NewStrategy(BaseStrategy):
    def calculate_positions(self, universe: List[str]) -> Dict[str, float]:
        # Implementation here
        pass
```

### 3. Configuration
```json
{
  "new_feature": {
    "enabled": true,
    "parameter": "value"
  }
}
```

## 📝 Commit Guidelines

### Commit Messages
Use conventional commit format:
```
type(scope): description

Examples:
feat(kelly): add Kelly Criterion position sizing
fix(data): handle missing market data gracefully
docs(readme): update installation instructions
```

### Types
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements

## 🚨 Security Guidelines

### API Keys
- Never commit API keys or credentials
- Use environment variables or secure config files
- Document required environment variables

### Data Handling
- Validate all user inputs
- Sanitize data before processing
- Use secure communication protocols

### Financial Data
- Encrypt sensitive financial information
- Audit trail for all trading decisions
- Secure storage of historical data

## 📊 Performance Requirements

### Response Times
- Quick analysis: <3 minutes
- Comprehensive analysis: <15 minutes
- API responses: <5 seconds
- Dashboard loads: <2 seconds

### Accuracy Targets
- Win rate: >55% (validated with live data)
- Kelly Criterion: Conservative 50% multiplier
- Risk management: Dynamic limits based on performance

## 🤝 Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test Changes**
   ```bash
   pytest tests/ -v
   black core/
   isort core/
   ```

4. **Submit Pull Request**
   - Descriptive title and description
   - Link to relevant issues
   - Include test results

5. **Review Process**
   - Code review by maintainers
   - Automated test validation
   - Performance impact assessment

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/InvestmentAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/InvestmentAI/discussions)
- **Documentation**: [docs/README.md](docs/README.md)

## 🏷️ Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update `CHANGELOG.md`
3. **Testing**: Full test suite validation
4. **Release**: Create GitHub release with notes

## 📋 Issue Templates

### Bug Report
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Relevant logs or screenshots

### Feature Request  
- Clear description of the feature
- Use case and business justification
- Implementation suggestions
- Potential impact on existing features

---

**Thank you for contributing to InvestmentAI!**

*Every contribution helps make the system more reliable, accurate, and beneficial for intelligent investing.*