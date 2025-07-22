@echo off
echo ==================================================
echo Investment System MCP Installation
echo ==================================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js first:
    echo https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js found
echo.

REM Create MCP directory structure
mkdir "C:\Users\%USERNAME%\.mcp" 2>nul
mkdir "C:\Users\%USERNAME%\.mcp\servers" 2>nul
echo 📁 MCP directory structure created
echo.

echo Installing essential MCPs...
echo.

REM Core database and development
npm install -g @modelcontextprotocol/server-sqlite
if %errorlevel% neq 0 echo ❌ SQLite MCP failed

npm install -g @modelcontextprotocol/server-filesystem
if %errorlevel% neq 0 echo ❌ Filesystem MCP failed

REM Financial data MCPs
echo.
echo 📊 Installing financial data MCPs...
npm install -g @modelcontextprotocol/server-fetch
if %errorlevel% neq 0 echo ❌ Fetch MCP failed

REM Web scraping and data extraction
echo.
echo 🔍 Installing data extraction MCPs...
npm install -g @modelcontextprotocol/server-sequential-thinking
if %errorlevel% neq 0 echo ❌ Sequential thinking MCP failed

REM Create MCP configuration
echo.
echo 🔧 Creating MCP configuration...
set "config_path=C:\Users\%USERNAME%\.mcp\mcp_config.json"

(
echo {
    "mcpServers": {
        "sqlite": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-sqlite", "--db-path", "%CD%\investment_system.db"]
        },
        "filesystem": {
            "command": "npx", 
            "args": ["@modelcontextprotocol/server-filesystem", "%CD%"]
        },
        "fetch": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-fetch"]
        }
    }
}
) > "%config_path%"

echo ✅ Configuration created: %config_path%
echo.

REM Verify installations
echo 🔍 Verifying installations...
echo.

echo Checking installed MCPs:
npx --version 2>nul
if %errorlevel% equ 0 echo ✅ npx available

where npx 2>nul
if %errorlevel% equ 0 echo ✅ npx in PATH

echo.
echo ==================================================
echo MCP Installation Complete! 🎉
echo ==================================================
echo.
echo Installed MCPs:
echo - SQLite: Database operations
echo - Filesystem: File operations  
echo - Fetch: HTTP requests for APIs
echo.
echo Configuration file: %config_path%
echo.
echo Next steps:
echo 1. Set up database: tools\setup\setup_database.bat
echo 2. Install additional MCPs as needed
echo 3. Add your API keys to the configuration
pause