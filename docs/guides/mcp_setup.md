# MCP (Model Context Protocol) Setup Guide

## Installed MCP Servers

### ✅ Successfully Installed

**1. Filesystem MCP Server**
- **Command**: `npx -y @modelcontextprotocol/server-filesystem .`
- **Purpose**: File management, project organization
- **Status**: ✅ Active
- **Allowed Directory**: `C:\Users\jandr\Documents\ivan`

**2. Memory MCP Server**
- **Command**: `npx -y @modelcontextprotocol/server-memory`
- **Purpose**: Persistent memory and context storage
- **Status**: ✅ Active

**3. Twelve Data MCP Server**
- **Installation**: `uv tool install mcp-server-twelve-data`
- **Purpose**: Real-time financial market data
- **Status**: ✅ Installed (requires API key for activation)
- **Location**: `C:\Users\jandr\.local\bin\mcp-server-twelve-data.exe`

**4. Alpaca MCP Server**
- **Installation**: `npm install -g alpaca-mcp`
- **Purpose**: Stock trading automation and market data
- **Status**: ✅ Installed (requires API credentials for activation)

## Configuration Required

### PATH Setup
Add to PATH for command line access:
```bash
export PATH="C:\Users\jandr\.local\bin:$PATH"
```

### API Keys Needed

**Twelve Data API**
- Sign up at: https://twelvedata.com/
- Free tier: 800 API calls/day
- Configuration: Set `TWELVE_DATA_API_KEY` environment variable

**Alpaca Trading API**
- Sign up at: https://alpaca.markets/
- Paper trading available for testing
- Configuration: Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`

## Claude Configuration

Add to Claude's MCP configuration file:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:/Users/jandr/Documents/ivan"
      ]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "twelve-data": {
      "command": "mcp-server-twelve-data.exe",
      "args": ["-k", "YOUR_TWELVE_DATA_API_KEY"],
      "env": {
        "TWELVE_DATA_API_KEY": "your_api_key_here"
      }
    },
    "alpaca": {
      "command": "npx",
      "args": ["-y", "alpaca-mcp"],
      "env": {
        "ALPACA_API_KEY": "your_api_key_here",
        "ALPACA_SECRET_KEY": "your_secret_key_here",
        "ALPACA_PAPER": "true"
      }
    }
  }
}
```

## Available Financial MCP Servers

### Additional Servers to Consider

**1. Financial Datasets MCP**
- **Repository**: https://github.com/financial-datasets/mcp-server
- **Purpose**: Stock market API for AI agents
- **Installation**: Available via GitHub

**2. AlphaVantage MCP**
- **Purpose**: 100+ APIs for financial market data
- **Features**: Stock prices, fundamentals, technical indicators
- **Installation**: Available from community

**3. Polygon.io MCP**
- **Repository**: https://github.com/polygon-io/mcp_polygon
- **Purpose**: Real-time financial market data
- **Features**: Stocks, options, crypto, forex data

## Usage Examples

### Financial Data Queries
With Twelve Data MCP active, you can query:
- Real-time stock prices
- Historical data for analysis
- Market indicators
- Currency exchange rates

### Trading Automation
With Alpaca MCP active, you can:
- Check account balance
- Place paper trades for testing
- Monitor portfolio performance
- Get market data

### File Management
With Filesystem MCP active, you can:
- Organize research files
- Create investment tracking spreadsheets
- Save portfolio analysis reports

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider using paper trading initially
- Rotate API keys regularly

### Trading Safety
- Start with paper trading (virtual money)
- Set position size limits
- Use stop-loss orders
- Test strategies thoroughly before real money

## Next Steps

### Immediate Actions
1. **Get API Keys**:
   - Sign up for Twelve Data (free tier)
   - Sign up for Alpaca (paper trading)

2. **Configure Environment**:
   - Set up environment variables
   - Update Claude MCP configuration
   - Test each server connection

3. **Start Using**:
   - Query real-time stock prices for your watchlist
   - Test paper trading with small amounts
   - Set up automated portfolio tracking

### Future Enhancements

**Additional MCP Servers**:
- News aggregation for market sentiment
- Economic calendar for market events
- Cryptocurrency data if expanding portfolio
- Portfolio analytics and backtesting tools

**Automation Opportunities**:
- Daily portfolio value tracking
- Automated rebalancing alerts
- Market data collection for analysis
- Performance reporting generation

## Troubleshooting

### Common Issues

**MCP Server Not Responding**:
- Check PATH configuration
- Verify API keys are set correctly
- Restart Claude after configuration changes

**Permission Errors**:
- Ensure filesystem permissions are correct
- Run as administrator if needed
- Check antivirus software interference

**API Rate Limits**:
- Monitor API usage
- Implement caching for frequent queries
- Consider upgrading to paid tiers if needed

### Support Resources
- MCP Documentation: https://modelcontextprotocol.io/
- Community GitHub: https://github.com/modelcontextprotocol/servers
- Twelve Data Docs: https://twelvedata.com/docs
- Alpaca API Docs: https://alpaca.markets/docs

This MCP setup provides a powerful foundation for automated financial research, portfolio tracking, and investment management for your Paraguay-based investment strategy.