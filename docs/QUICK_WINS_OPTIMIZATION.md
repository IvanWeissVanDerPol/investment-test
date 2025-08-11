# Quick Wins - Immediate Optimization Opportunities

## 1-Day Improvements (High Impact, Low Risk)

### 1. Create Module Dependency Map
```python
# src/investment_system/core/dependencies.py
"""
Central dependency registry to track and manage module relationships.
"""

DEPENDENCY_MAP = {
    'core.contracts': {
        'dependents': [
            'services.signal_service',
            'services.billing_service',
            'services.user_service',
            'api.handlers.signals',
            'api.handlers.billing',
            'infrastructure.crud',
            'repositories.signal_repository',
            'repositories.user_repository',
            'ml.signal_generator',
            'pipeline.analyze',
            'sonar.signal_processor',
            'sonar.components.strategy_executor',
            'sonar.components.portfolio_manager',
            'sonar.api',
            'main'
        ],
        'external_deps': ['pydantic', 'enum', 'datetime'],
        'stability': 'STABLE',  # STABLE, UNSTABLE, DEPRECATED
        'owner': 'core-team'
    },
    'cache': {
        'dependents': [
            'services.signal_service',
            'api.handlers.signals',
            'repositories.base',
            'ml.signal_generator',
            'pipeline.ingest',
            'sonar.components.data_handler',
            'sonar.api',
            'main',
            'infrastructure.database_session'
        ],
        'external_deps': ['redis', 'pickle', 'json'],
        'stability': 'STABLE',
        'owner': 'infrastructure-team'
    }
}

def check_dependency_health():
    """Check for dependency issues and bottlenecks."""
    issues = []
    for module, info in DEPENDENCY_MAP.items():
        if len(info['dependents']) > 10:
            issues.append(f"HIGH_COUPLING: {module} has {len(info['dependents'])} dependents")
        if info['stability'] == 'UNSTABLE' and len(info['dependents']) > 5:
            issues.append(f"RISK: Unstable module {module} has {len(info['dependents'])} dependents")
    return issues
```

### 2. Add Import Linting Rules
```python
# .pre-commit-config.yaml addition
- repo: local
  hooks:
    - id: check-imports
      name: Check import dependencies
      entry: python scripts/check_imports.py
      language: python
      files: \.py$
```

```python
# scripts/check_imports.py
import ast
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = {
    'services': ['services'],  # Services shouldn't import other services
    'api': ['infrastructure.database'],  # API shouldn't directly access DB
    'core': ['services', 'api', 'infrastructure'],  # Core shouldn't depend on outer layers
}

def check_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    module_path = str(filepath).replace('/', '.').replace('\\', '.')
    layer = module_path.split('.')[2] if len(module_path.split('.')) > 2 else None
    
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if layer in FORBIDDEN_IMPORTS:
                    for forbidden in FORBIDDEN_IMPORTS[layer]:
                        if forbidden in alias.name:
                            issues.append(f"{filepath}: {layer} imports forbidden {alias.name}")
    return issues

if __name__ == "__main__":
    issues = []
    for py_file in Path('src').rglob('*.py'):
        issues.extend(check_file(py_file))
    
    if issues:
        print("Import violations found:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
```

### 3. Create Facade Pattern for Core.Contracts
```python
# src/investment_system/core/contracts/__init__.py
"""
Facade for contracts module - maintains backward compatibility
while allowing internal refactoring.
"""

# Internal organization (new structure)
from .user import User, UserTier, UserCreate, UserUpdate
from .trading import TradingSignal, SignalType, MarketIndicator
from .billing import Subscription, BillingPlan, PaymentMethod
from .market import MarketData, PricePoint, Volume

# Maintain backward compatibility
__all__ = [
    # User domain
    'User', 'UserTier', 'UserCreate', 'UserUpdate',
    # Trading domain
    'TradingSignal', 'SignalType', 'MarketIndicator',
    # Billing domain
    'Subscription', 'BillingPlan', 'PaymentMethod',
    # Market domain
    'MarketData', 'PricePoint', 'Volume',
]

# Deprecation warnings for direct access
def __getattr__(name):
    import warnings
    warnings.warn(
        f"Importing {name} from core.contracts is deprecated. "
        f"Use core.contracts.{{domain}} instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Still return the object for compatibility
    return globals()[name]
```

## 1-Week Improvements (Medium Impact, Low Risk)

### 1. Implement Service Registry Pattern
```python
# src/investment_system/core/service_registry.py
from typing import Dict, Any, Type
from functools import lru_cache

class ServiceRegistry:
    """Central registry for all services - reduces coupling."""
    
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, service_class: Type):
        """Register a service class."""
        cls._factories[name] = service_class
    
    @classmethod
    @lru_cache(maxsize=None)
    def get(cls, name: str, **kwargs):
        """Get or create a service instance."""
        if name not in cls._services:
            if name not in cls._factories:
                raise ValueError(f"Service {name} not registered")
            cls._services[name] = cls._factories[name](**kwargs)
        return cls._services[name]
    
    @classmethod
    def reset(cls):
        """Reset all services (useful for testing)."""
        cls._services.clear()
        cls.get.cache_clear()

# Usage in services
from investment_system.core.service_registry import ServiceRegistry

# Registration (at startup)
ServiceRegistry.register('signal', SignalService)
ServiceRegistry.register('billing', BillingService)

# Usage (anywhere)
signal_service = ServiceRegistry.get('signal')
```

### 2. Add Dependency Metrics Dashboard
```python
# src/investment_system/monitoring/dependency_metrics.py
import ast
from pathlib import Path
from collections import defaultdict
import json

class DependencyAnalyzer:
    def __init__(self, src_path="src/investment_system"):
        self.src_path = Path(src_path)
        self.import_graph = defaultdict(set)
        self.module_sizes = {}
        
    def analyze(self):
        """Analyze all Python files for dependencies."""
        for py_file in self.src_path.rglob("*.py"):
            self._analyze_file(py_file)
        return self._generate_report()
    
    def _analyze_file(self, filepath):
        with open(filepath) as f:
            content = f.read()
            self.module_sizes[str(filepath)] = len(content.splitlines())
            
        try:
            tree = ast.parse(content)
            module_name = self._path_to_module(filepath)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('investment_system'):
                            self.import_graph[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('investment_system'):
                        self.import_graph[module_name].add(node.module)
        except:
            pass  # Skip files with syntax errors
    
    def _generate_report(self):
        # Calculate metrics
        dependency_counts = {
            module: len(deps) for module, deps in self.import_graph.items()
        }
        
        # Find modules imported by many others
        imported_by = defaultdict(list)
        for module, deps in self.import_graph.items():
            for dep in deps:
                imported_by[dep].append(module)
        
        return {
            'total_modules': len(self.module_sizes),
            'total_dependencies': sum(dependency_counts.values()),
            'most_dependencies': sorted(
                dependency_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'most_imported': sorted(
                [(k, len(v)) for k, v in imported_by.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'largest_modules': sorted(
                self.module_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'coupling_score': self._calculate_coupling_score()
        }
    
    def _calculate_coupling_score(self):
        """Calculate overall coupling score (0-10, 10 being best)."""
        avg_deps = sum(len(deps) for deps in self.import_graph.values()) / len(self.import_graph)
        if avg_deps < 3:
            return 10
        elif avg_deps < 5:
            return 8
        elif avg_deps < 8:
            return 6
        elif avg_deps < 12:
            return 4
        else:
            return 2

# Generate HTML report
def generate_html_report():
    analyzer = DependencyAnalyzer()
    report = analyzer.analyze()
    
    html = f"""
    <html>
    <head><title>Dependency Analysis</title></head>
    <body>
        <h1>Investment System - Dependency Analysis</h1>
        <h2>Overall Metrics</h2>
        <ul>
            <li>Total Modules: {report['total_modules']}</li>
            <li>Total Dependencies: {report['total_dependencies']}</li>
            <li>Coupling Score: {report['coupling_score']}/10</li>
        </ul>
        <h2>Most Complex Modules (by dependencies)</h2>
        <ol>
            {''.join(f"<li>{m}: {c} dependencies</li>" for m, c in report['most_dependencies'])}
        </ol>
        <h2>Most Imported Modules</h2>
        <ol>
            {''.join(f"<li>{m}: imported by {c} modules</li>" for m, c in report['most_imported'])}
        </ol>
    </body>
    </html>
    """
    
    with open('dependency_report.html', 'w') as f:
        f.write(html)
```

## Monitoring & Validation

### Automated Checks (Add to CI)
```yaml
# .github/workflows/dependency-check.yml
name: Dependency Health Check

on: [push, pull_request]

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check import violations
        run: python scripts/check_imports.py
        
      - name: Generate dependency report
        run: |
          python -m investment_system.monitoring.dependency_metrics
          
      - name: Check coupling thresholds
        run: |
          python -c "
          from investment_system.core.dependencies import check_dependency_health
          issues = check_dependency_health()
          if issues:
              print('Dependency issues found:')
              for issue in issues:
                  print(f'  - {issue}')
              exit(1)
          "
```

## Expected Improvements

### Immediate (Day 1)
- **Visibility**: Clear understanding of dependencies
- **Prevention**: Linting prevents new coupling issues
- **Compatibility**: Facade pattern allows gradual migration

### Short-term (Week 1)
- **Testability**: Service registry enables easy mocking
- **Metrics**: Dashboard shows coupling trends
- **Maintainability**: Clear module boundaries

### Medium-term (Month 1)
- **Performance**: Better caching with clear dependencies
- **Reliability**: Fewer unexpected side effects
- **Development Speed**: Faster feature development with clear contracts

## Success Metrics

Track these metrics weekly:
1. **Average module dependencies**: Target < 5
2. **Maximum module dependents**: Target < 10
3. **Service interdependencies**: Target 0
4. **Test execution time**: Should decrease by 20%
5. **Bug fix time**: Should decrease by 30%

## Next Steps

1. **Today**: Implement dependency map and import linting
2. **This Week**: Add service registry and metrics dashboard
3. **Next Week**: Begin contract refactoring with facade pattern
4. **Month 1**: Full dependency injection implementation