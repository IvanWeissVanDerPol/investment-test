# Investment System MCP Usage Guide

## 🎯 Overview
The investment system now includes comprehensive MCP (Model Context Protocol) support for enhanced automation and structured workflows.

## 📦 Installed MCPs

### ✅ Official MCPs
- **@modelcontextprotocol/server-filesystem** - File system operations
- **@modelcontextprotocol/server-sequential-thinking** - Advanced reasoning

### ✅ Custom Investment MCP
- **investment_mcp.py** - Database and configuration access

## 🔧 Configuration

### MCP Configuration File
Location: `.claude/mcp_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "sequential-thinking": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "investment-core": {
      "command": "python",
      "args": ["mcp/investment_mcp.py"]
    }
  }
}
```

## 🚀 Quick Start

### 1. Set Up Database
```bash
# Run from project root
python core/database/setup.py
# Or use Windows batch file:
tools\setup\setup_database.bat
```

### 2. Test MCP Server
```bash
# Get portfolio summary
python mcp/investment_mcp.py portfolio

# Get target stocks
python mcp/investment_mcp.py stocks

# Get user configuration
python mcp/investment_mcp.py profile
```

### 3. Run Workflows
```bash
# Comprehensive analysis
tools\workflows\run_analysis.bat

# Portfolio monitoring
tools\workflows\monitor_portfolio.bat

# Data collection
tools\workflows\collect_data.bat
```

## 🎯 Available MCP Commands

### Portfolio Management
```bash
python mcp/investment_mcp.py portfolio
# Returns: portfolio summary, total securities, stocks vs ETFs
```

### Stock Selection
```bash
python mcp/investment_mcp.py stocks
# Returns: target AI/robotics stocks with metadata
```

### Configuration Access
```bash
python mcp/investment_mcp.py profile
# Returns: user profile and investment goals

python mcp/investment_mcp.py settings
# Returns: analysis thresholds and alert settings
```

### Institutional Data
```bash
python mcp/investment_mcp.py funds
# Returns: smart money institutions and priorities

python mcp/investment_mcp.py defense
# Returns: defense contractors and AI focus
```

### Ethics Configuration
```bash
python mcp/investment_mcp.py ethics
# Returns: blacklist, preferred/blocked categories
```

### Keywords Analysis
```bash
python mcp/investment_mcp.py keywords ai
# Returns: AI-related keywords for analysis

python mcp/investment_mcp.py keywords sustainability
# Returns: sustainability-related keywords
```

## 🔄 Workflow Integration

### Daily Analysis Workflow
1. **Data Collection**: `collect_data.bat`
2. **Analysis**: `run_analysis.bat`
3. **Monitoring**: `monitor_portfolio.bat`

### Weekly Review Workflow
1. **Portfolio Review**: MCP portfolio command
2. **Institution Tracking**: MCP funds command
3. **Ethics Check**: MCP ethics command

### Monthly Deep Dive
1. **Comprehensive Analysis**: Full system run
2. **Sector Analysis**: Defense contractors review
3. **Settings Optimization**: Configuration review

## 🛠 IDE Integration

### Claude Desktop
1. Copy `.claude/mcp_config.json` to your Claude Desktop config
2. Restart Claude Desktop
3. MCP tools will appear in the interface

### Cursor
1. Settings > MCP > Add from file
2. Select `.claude/mcp_config.json`
3. MCP tools available in chat

### Windsurf
1. Settings > MCP > Add server
2. Configure using provided JSON

## 📊 MCP Benefits

### ✅ Enhanced Capabilities
- **Structured data access** via database queries
- **Real-time configuration** updates
- **Automated workflows** with batch processing
- **Integration** with multiple IDEs and tools

### ✅ Workflow Improvements
- **Consistent data access** across tools
- **Reduced manual steps** in analysis
- **Better error handling** and validation
- **Extensible architecture** for new features

## 🔍 Troubleshooting

### Common Issues

**Database not found**:
```bash
# Ensure database is set up
python core/database/setup.py
```

**MCP server not responding**:
```bash
# Check Python path
python -c "import mcp.investment_mcp; print('MCP ready')"
```

**Configuration issues**:
```bash
# Verify MCP config
python -c "import json; print(json.load(open('.claude/mcp_config.json', 'r')))"
```

## 🚀 Advanced Usage

### Custom MCP Development
Create new MCP servers in `mcp/` directory following the `investment_mcp.py` pattern.

### API Integration
Extend MCP servers to integrate with:
- Alpha Vantage
- Yahoo Finance
- Interactive Brokers TWS
- Social sentiment APIs

### Monitoring Integration
Use MCP servers for:
- Real-time portfolio monitoring
- Alert system integration
- Performance tracking
- Risk assessment automation

## 📈 Performance Tips

1. **Cache results** using database caching
2. **Batch operations** with workflow scripts
3. **Parallel processing** for large datasets
4. **Error handling** with comprehensive validation

## 🎯 Next Steps

1. **Install additional MCPs** as needed
2. **Customize workflows** for your specific needs
3. **Extend MCP servers** for new data sources
4. **Integrate** with external trading platforms
5. **Automate** daily/weekly/monthly routines

The MCP system is now ready for production use with your investment analysis system!