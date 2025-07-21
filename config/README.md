# Investment Analysis System - Configuration Guide

## Overview

This directory contains the configuration files for Ivan's AI-powered Investment Portfolio Management System. The system has undergone a major refactoring to eliminate duplicates and improve maintainability.

## 🚀 **Current Structure (Recommended)**

The system now uses **3 consolidated configuration files** that eliminate all redundancy:

### 1. `master_data.json` (11.7KB)
**Single source of truth for all investment data**

- **Stock Universe**: Organized by categories (AI companies, semiconductors, robotics, defense, green energy, healthcare)
- **Company Metadata**: Enhanced with AI focus levels, government contract exposure, subsectors, CIK codes
- **ETF/Fund Information**: Complete fund data with expense ratios, focus areas, and holdings
- **Smart Money Tracking**: Fund priorities, key holdings, and investment focuses
- **Ethics Screening**: ESG preferences, blacklists with alternatives, green investment targets
- **Sector Mappings**: Comprehensive sector and subsector classifications

### 2. `system_config.json` (20.1KB)
**Technical and operational configuration**

- **Network Settings**: Interactive Brokers connection, API endpoints, SSL settings
- **API Configuration**: All API providers (Alpha Vantage, Finnhub, Claude, etc.) with rate limits
- **Timeframes**: Data collection periods, cache settings, monitoring intervals
- **Analysis Parameters**: Technical indicators, confidence thresholds, analysis weights
- **Risk Management**: VaR settings, correlation limits, stress test thresholds
- **Social Platforms**: Reddit subreddits, Twitter terms, YouTube channels
- **File Patterns**: Report naming, log rotation, cache management

### 3. `user_profile.json` (6.8KB)
**Personal preferences and portfolio settings**

- **Personal Info**: User details, email, timezone, account information
- **Portfolio Settings**: Balance allocation, risk tolerance, position limits
- **Investment Goals**: AI/robotics focus, green investments, smart money following
- **Ethics Preferences**: ESG weights, sustainability priorities, avoidance criteria
- **Trading Preferences**: Order types, confirmation settings, daily limits
- **Watchlists**: Multiple lists (primary, AI, green, defense, ETF)
- **Notifications**: Alert preferences, reporting schedules, delivery settings

## 📚 **Configuration Loader**

Use the `config_loader.py` module to access configurations:

```python
from config.config_loader import config_manager

# Get stock symbols by category
ai_stocks = config_manager.get_stock_symbols('ai_companies')
green_stocks = config_manager.get_stock_symbols('green_energy')

# Get company metadata
nvda_info = config_manager.get_company_metadata('NVDA')

# Get user preferences
watchlist = config_manager.get_user_watchlist('ai_watchlist')
allocation_targets = config_manager.get_user_allocation_targets()

# Get system settings
api_config = config_manager.get_api_config('finnhub')
ib_config = config_manager.get_network_config('interactive_brokers')
```

## ⚠️ **Legacy Files (Deprecated)**

The following files contain duplicate/fragmented data and should **NOT** be used for new development:

### Legacy Configuration Files:
- `config.json` - Original user and system settings (mixed structure)
- `data.json` - Previous attempt at business data consolidation
- `system.json` - Previous attempt at technical settings consolidation
- `analysis.json` - Previous attempt at analysis parameters consolidation
- `content.json` - Previous attempt at content/social platform settings

### Legacy Data Files:
- `expanded_stock_universe.json` - Detailed stock categorization (superseded by master_data.json)
- `comprehensive_sectors.json` - Extensive sector mappings (integrated into master_data.json)
- `investment_funds_and_companies.json` - Fund and ETF data (consolidated into master_data.json)

## 🔄 **Migration Status**

| Component | Status | Action Required |
|-----------|--------|-----------------|
| **Configuration Structure** | ✅ Complete | Use new 3-file structure |
| **Config Loader** | ✅ Updated | Use updated `config_loader.py` |
| **Source Code Migration** | 🔄 In Progress | Update Python modules to use config_loader |
| **Legacy File Cleanup** | ⏳ Pending | Remove deprecated files after migration |

## 🎯 **Key Benefits of New Structure**

1. **Zero Redundancy**: Each data point exists in exactly one place
2. **55% Size Reduction**: From ~85KB to ~38KB while adding functionality  
3. **Logical Organization**: Related settings grouped together
4. **Enhanced Metadata**: Richer company information with AI focus and government contract levels
5. **User-Centric Design**: Personal preferences separated from system settings
6. **Maintainable**: Easy to update and extend without conflicts

## 📖 **Configuration Details**

### Stock Categories in `master_data.json`:
- **AI Companies**: Mega-cap, large-cap, mid-cap, small-cap, specialized
- **Semiconductors**: Major chips, memory/storage, equipment, design tools
- **Robotics/Automation**: Industrial, medical, service, agricultural, warehouse
- **Defense/Aerospace**: Prime contractors, cybersecurity, space/satellite, drones
- **Green Energy**: Solar, wind, EVs, energy storage, clean tech, materials
- **Healthcare/Biotech**: Gene therapy, medical devices, telemedicine, pharmaceuticals

### ETF Categories:
- **AI/Robotics**: ARKQ, BOTZ, ROBO, IRBO, UBOT, THNQ, QTUM
- **Technology**: QQQ, XLK, VGT, SOXX, SMH, CLOU, HACK
- **Green Energy**: ICLN, QCLN, PBW, TAN, FAN, LIT, GRID
- **Defense**: ITA, XAR, PPA, DFEN

### Smart Money Funds Tracked:
- ARK Invest (Disruptive Innovation)
- Tiger Global Management (Technology)
- Coatue Management (Technology)
- Berkshire Hathaway (Value)
- Andreessen Horowitz (Venture Capital)
- Sequoia Capital (Venture Capital)

## 🔧 **Environment Variables**

Set these environment variables for API access:

```bash
# Required
CLAUDE_API_KEY=your_claude_api_key
FINNHUB_API_KEY=your_finnhub_api_key

# Optional
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_API_KEY=your_polygon_key
NEWSAPI_KEY=your_news_api_key
TWELVEDATA_API_KEY=your_twelvedata_key
WHALEWISDOM_API_KEY=your_whalewisdom_key
```

## 🚨 **Important Notes**

1. **Use Only New Structure**: The 3-file structure (`master_data.json`, `system_config.json`, `user_profile.json`) is the current standard
2. **Legacy Files**: Old configuration files are kept temporarily for reference but should not be modified
3. **API Keys**: Never commit actual API keys to version control - use environment variables
4. **Validation**: The config_loader includes validation for all configuration files
5. **Caching**: Configurations are cached for 30 minutes to improve performance

## 📞 **Support**

For questions about the configuration system:
1. Check the `config_loader.py` documentation
2. Review the validation methods for required fields
3. Use the convenience functions for common operations
4. Ensure environment variables are properly set

---

**Last Updated**: January 2025  
**Configuration Version**: 3.0 (3-file structure)  
**System**: Ivan's AI Investment Portfolio Management System
