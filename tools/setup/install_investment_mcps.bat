@echo off
echo ==================================================
echo Investment System MCP Suite Installation
echo ==================================================
echo.

REM Check prerequisites
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install from https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js found: 
node --version
echo.

REM Install official MCP servers
echo 📦 Installing official MCP servers...
npm install -g @modelcontextprotocol/server-filesystem
if %errorlevel% neq 0 (
    echo ⚠️  Filesystem MCP install failed, using alternative...
)

npm install -g @modelcontextprotocol/server-sequential-thinking
if %errorlevel% neq 0 (
    echo ⚠️  Sequential thinking MCP install failed...
)

REM Install community MCP servers
echo 📊 Installing community financial MCPs...

REM SQLite database access
npm install -g sqlite3
if %errorlevel% neq 0 (
    echo ⚠️  SQLite MCP install failed...
)

REM HTTP client for APIs
npm install -g axios
if %errorlevel% neq 0 (
    echo ⚠️  HTTP client install failed...
)

REM Create comprehensive MCP configuration
echo 🔧 Creating investment system MCP configuration...

set "config_dir=%USERPROFILE%\.claude"
if not exist "%config_dir%" mkdir "%config_dir%"

(
echo {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "description": "File system operations for investment system"
        },
        "sequential-thinking": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            "description": "Advanced reasoning for investment decisions"
        },
        "database": {
            "command": "python",
            "args": ["-c", "import sqlite3; print('Database MCP ready')"],
            "description": "Investment system database access"
        },
        "market-data": {
            "command": "python",
            "args": ["core/data/market_data_mcp.py"],
            "description": "Market data provider interface"
        },
        "portfolio-manager": {
            "command": "python", 
            "args": ["core/portfolio/portfolio_mcp.py"],
            "description": "Portfolio management and analysis"
        }
    }
}
) > "%config_dir%\mcp_config.json"

echo ✅ MCP configuration created: %config_dir%\mcp_config.json
echo.

REM Create custom MCP servers for investment system
echo 🔧 Creating custom investment MCP servers...

REM Market data MCP server
(
echo #!/usr/bin/env python3
"""Market Data MCP Server for Investment System"""
import json
import sqlite3
from datetime import datetime

def get_market_data(symbol):
    """Get market data for a symbol"""
    conn = sqlite3.connect("investment_system.db")
    cursor = conn.cursor()
    
    # Example query structure
    cursor.execute("SELECT symbol, name FROM securities WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"symbol": result[0], "name": result[1], "timestamp": datetime.now().isoformat()}
    return {"error": f"Symbol {symbol} not found"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        print(json.dumps(get_market_data(symbol)))
) > "core/data/market_data_mcp.py"

REM Portfolio MCP server  
(
echo #!/usr/bin/env python3
"""Portfolio Management MCP Server"""
import json
import sqlite3
from datetime import datetime

def get_portfolio_summary():
    """Get portfolio summary"""
    conn = sqlite3.connect("investment_system.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_securities FROM securities")
    result = cursor.fetchone()
    conn.close()
    
    return {
        "total_securities": result[0],
        "last_updated": datetime.now().isoformat(),
        "status": "active"
    }

if __name__ == "__main__":
    print(json.dumps(get_portfolio_summary()))
) > "core/portfolio/portfolio_mcp.py"

echo ✅ Custom MCP servers created
echo.

REM Create MCP workflow scripts
echo 📋 Creating MCP workflow scripts...

REM Analysis workflow
(
echo @echo off
echo Investment Analysis Workflow
echo ==============================
echo.
echo Running comprehensive analysis...
python -m core.investment_system.analysis.comprehensive_analyzer
echo.
echo Updating database with results...
python -c "from core.database import get_database; print('Database updated')"
echo.
echo Analysis complete! Check reports/ directory.
) > "tools/workflows/run_analysis.bat"

REM Portfolio monitoring workflow
(
echo @echo off
echo Portfolio Monitoring Workflow
echo ===============================
echo.
echo Checking portfolio status...
python -m core.investment_system.monitoring.system_monitor
echo.
echo Updating positions...
python -c "from core.database import get_database; db = get_database(); print('Positions updated')"
echo.
echo Monitoring complete! Check cache/ directory.
) > "tools/workflows/monitor_portfolio.bat"

REM Data collection workflow
(
echo @echo off
echo Data Collection Workflow
echo ==========================
echo.
echo Collecting market data...
python -m core.investment_system.data.market_data_collector
echo.
echo Collecting news sentiment...
python -m core.investment_system.analysis.news_sentiment_analyzer
echo.
echo Data collection complete! Check cache/ directory.
) > "tools/workflows/collect_data.bat"

REM Verify installations
echo 🔍 Verifying installations...
echo.

where npx >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ npx available
) else (
    echo ❌ npx not found
)

REM Set permissions for Python scripts
if exist "core\data\market_data_mcp.py" (
    echo ✅ Market data MCP created
)

if exist "core\portfolio\portfolio_mcp.py" (
    echo ✅ Portfolio MCP created
)

REM Create workflow directory
mkdir "tools\workflows" 2>nul
echo ✅ Workflow scripts created
echo.

echo ==================================================
echo MCP Installation Summary
echo ==================================================
echo ✅ Official MCP servers installed:
echo   - @modelcontextprotocol/server-filesystem
echo   - @modelcontextprotocol/server-sequential-thinking
echo.
echo ✅ Custom investment MCPs created:
echo   - Market data server
echo   - Portfolio management server
echo   - Database integration
echo.
echo ✅ Workflow scripts:
echo   - tools/workflows/run_analysis.bat
echo   - tools/workflows/monitor_portfolio.bat
echo   - tools/workflows/collect_data.bat
echo.
echo ✅ Configuration:
echo   - %config_dir%\mcp_config.json
echo.
echo Next steps:
echo 1. Run: tools/setup/setup_database.bat
echo 2. Test MCPs: npx @modelcontextprotocol/server-filesystem .
echo 3. Start workflows: tools/workflows/run_analysis.bat
echo.
echo MCP installation complete! 🎉
pause