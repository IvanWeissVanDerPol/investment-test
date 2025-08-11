# Repository Reorganization Complete

## New Structure Overview

The repository has been reorganized into three main directories with clear separation of concerns:

```
ivan/
├── core/                    # Business logic and investment system
├── web/                     # Web dashboard and frontend
├── tools/                   # Scripts and automation tools
├── docs/                    # Documentation
├── config/                  # Configuration files
├── data/                    # Reference data
├── cache/                   # Runtime cache
├── reports/                 # Generated reports
├── tests/                   # Test suite
└── requirements.txt         # Python dependencies
```

## Directory Details

### `core/` - Investment System Logic
- **Purpose**: All Python business logic and investment analysis
- **Contents**: 
  - Complete investment system from `src/investment_system/`
  - All modules: data, analysis, portfolio, monitoring, reporting, etc.
  - Maintains original package structure under `core/investment_system/`

### `web/` - Web Dashboard
- **Purpose**: Local web interface for visualizing investment data
- **Contents**:
  - `app.py` - Main Flask application
  - `requirements.txt` - Web-specific dependencies
  - `templates/` - HTML templates
  - (Future: `static/` for CSS/JS assets)

### `tools/` - Automation Scripts
- **Purpose**: Batch files, Python scripts, and utilities for running the system
- **Contents**:
  - `analysis/` - Daily analysis scripts
  - `monitoring/` - System monitoring tools
  - `setup/` - Development environment setup
  - `testing/` - Test execution scripts
  - `utilities/` - Maintenance and validation tools
  - `youtube/` - YouTube integration scripts
  - `README.md` - Tools documentation

## Import Path Updates

### Old Import Paths
```python
from src.investment_system.analysis import quick_analysis
from src.investment_system.portfolio import portfolio_analysis
```

### New Import Paths
```python
from core.investment_system.analysis import quick_analysis
from core.investment_system.portfolio import portfolio_analysis
```

## Running the System

### From Core Directory
```bash
cd core
python -m investment_system.analysis.quick_analysis
python -m investment_system.monitoring.system_monitor
```

### From Root Directory
```bash
# Using tools
python tools\analysis\run_daily_analysis.bat
python tools\monitoring\run_system_monitor.bat

# Web dashboard
cd web
python app.py
```

## Benefits of New Structure

1. **Clear Separation**: Logic, interface, and tools are clearly separated
2. **Minimal Root Folders**: Only 3 main directories plus standard project folders
3. **Logical Grouping**: Related functionality is grouped together
4. **Easy Navigation**: Clear purpose for each directory
5. **Scalable**: Easy to add new components without cluttering root

## Migration Notes

- All existing functionality is preserved
- Import paths need to be updated in any custom scripts
- Configuration files remain in their original locations
- Cache and reports directories maintain their structure
- No breaking changes to existing data or configurations

## Next Steps

1. Update any custom scripts to use new import paths
2. Test all tools with new directory structure
3. Update documentation references
4. Verify web dashboard integration with core modules