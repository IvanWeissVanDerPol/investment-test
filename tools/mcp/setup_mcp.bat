@echo off
echo ==================================================
echo Investment System MCP Setup Complete ✅
echo ==================================================
echo.

echo 📦 MCP Servers Installed:
echo   ✅ @modelcontextprotocol/server-filesystem
echo   ✅ @modelcontextprotocol/server-sequential-thinking
echo   ✅ Custom investment system MCP
echo.
echo 🔧 Configuration:
echo   📁 Config file: .claude\mcp_config.json
echo   📁 Custom MCP: mcp\investment_mcp.py
echo.
echo 🎯 Available MCP Commands:
echo   - portfolio    : Get portfolio summary
echo   - stocks       : Get target AI/robotics stocks
echo   - profile      : Get user configuration
echo   - settings     : Get analysis settings
echo   - funds        : Get smart money institutions
echo   - defense      : Get defense contractors
echo   - ethics       : Get ethics configuration
echo   - keywords     : Get analysis keywords
echo.
echo 🚀 Usage Examples:
echo   python mcp/investment_mcp.py portfolio
echo   python mcp/investment_mcp.py stocks
echo   python mcp/investment_mcp.py keywords ai
echo.
echo 🔗 Integration:
echo   Claude Desktop: .claude\mcp_config.json
echo   Cursor: Settings > MCP > Add from file
echo   Windsurf: Settings > MCP > Add server
echo.
echo Next steps:
echo 1. Set up database: tools\setup\setup_database.bat
echo 2. Test MCP: python mcp/investment_mcp.py portfolio
echo 3. Run workflows: tools\workflows\*.bat
echo.
pause