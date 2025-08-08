# Web Dashboard API Endpoints

## Core Data Endpoints

### Portfolio Overview
```
GET /api/portfolio/overview
```
**Response:**
```json
{
  "total_value": 900.00,
  "cash_balance": 100.00,
  "invested_amount": 800.00,
  "daily_change": 15.50,
  "daily_change_percent": 1.75,
  "risk_score": "medium",
  "last_updated": "2025-07-21T14:30:00Z"
}
```

### Current Positions
```
GET /api/portfolio/positions
```
**Response:**
```json
{
  "positions": [
    {
      "symbol": "NVDA",
      "shares": 2.5,
      "current_price": 120.50,
      "total_value": 301.25,
      "gain_loss": 25.50,
      "gain_loss_percent": 9.25,
      "weight": 33.5
    }
  ],
  "total_positions": 8,
  "last_updated": "2025-07-21T14:30:00Z"
}
```

### AI Recommendations
```
GET /api/ai/recommendations
```
**Response:**
```json
{
  "recent_decisions": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "confidence": 0.85,
      "price_target": 125.00,
      "reasoning": "Strong AI sector momentum",
      "timestamp": "2025-07-21T14:00:00Z"
    }
  ],
  "pending_recommendations": 3,
  "last_analysis": "2025-07-21T14:30:00Z"
}
```

### Market Data
```
GET /api/market/data?symbols=NVDA,TSLA,MSFT
```
**Response:**
```json
{
  "market_data": [
    {
      "symbol": "NVDA",
      "price": 120.50,
      "change": 2.15,
      "change_percent": 1.82,
      "volume": 45000000,
      "timestamp": "2025-07-21T14:30:00Z"
    }
  ],
  "last_updated": "2025-07-21T14:30:00Z"
}
```

### Sentiment Analysis
```
GET /api/sentiment/summary
```
**Response:**
```json
{
  "overall_sentiment": "bullish",
  "sentiment_score": 0.72,
  "news_sentiment": 0.65,
  "social_sentiment": 0.78,
  "youtube_sentiment": 0.70,
  "top_positive": ["NVDA", "MSFT", "TSLA"],
  "top_negative": ["AAPL"],
  "last_updated": "2025-07-21T14:30:00Z"
}
```

### Risk Metrics
```
GET /api/risk/metrics
```
**Response:**
```json
{
  "portfolio_risk": "medium",
  "var_95": -45.20,
  "max_drawdown": -8.5,
  "sharpe_ratio": 1.25,
  "beta": 1.15,
  "sector_concentration": {
    "technology": 75,
    "healthcare": 15,
    "energy": 10
  },
  "last_updated": "2025-07-21T14:30:00Z"
}
```

### Smart Money Tracking
```
GET /api/smart-money/activity
```
**Response:**
```json
{
  "recent_activity": [
    {
      "fund": "ARK Invest",
      "symbol": "NVDA",
      "action": "BUY",
      "shares": 50000,
      "value": 6000000,
      "date": "2025-07-20",
      "confidence": "high"
    }
  ],
  "top_holders": ["NVDA", "TSLA", "MSFT"],
  "last_updated": "2025-07-21T14:30:00Z"
}
```

## Data Source Endpoints

### Cache Access
```
GET /api/cache/list
```
**Response:**
```json
{
  "cache_files": [
    {
      "filename": "ai_decisions_NVDA_hold_20250721.json",
      "size": 2048,
      "modified": "2025-07-21T14:30:00Z"
    }
  ]
}
```

```
GET /api/cache/file/<filename>
```
**Response:** Raw JSON content from specified cache file

### Report Access
```
GET /api/reports/list
```
**Response:**
```json
{
  "reports": [
    {
      "type": "daily",
      "filename": "daily_investment_report_20250721.json",
      "created": "2025-07-21T09:00:00Z"
    },
    {
      "type": "comprehensive",
      "filename": "comprehensive_analysis_20250721.json",
      "created": "2025-07-21T09:30:00Z"
    }
  ]
}
```

## Configuration Endpoints

### Get Settings
```
GET /api/config/settings
```
**Response:**
```json
{
  "user_profile": {
    "name": "Ivan",
    "risk_tolerance": "medium",
    "balance": 900.00,
    "rebalance_frequency": "quarterly"
  },
  "target_sectors": ["AI/Robotics", "Technology"],
  "alert_thresholds": {
    "price_change": 5.0,
    "risk_score": 7.0,
    "portfolio_variance": 15.0
  }
}
```

### Update Settings
```
POST /api/config/settings
```
**Request Body:**
```json
{
  "risk_tolerance": "high",
  "alert_thresholds": {
    "price_change": 7.0
  }
}
```

## Real-time Updates

### WebSocket Endpoint (Future)
```
ws://localhost:5000/ws/realtime
```
**Messages:**
- Portfolio updates
- New AI recommendations
- Alert notifications
- Market data changes

### Polling Endpoints
```
GET /api/updates/since/<timestamp>
```
**Response:**
```json
{
  "has_updates": true,
  "updates": [
    {
      "type": "price_update",
      "symbol": "NVDA",
      "old_price": 119.00,
      "new_price": 120.50,
      "timestamp": "2025-07-21T14:30:00Z"
    }
  ]
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "SYMBOL_NOT_FOUND",
    "message": "Stock symbol XYZ not found in portfolio",
    "timestamp": "2025-07-21T14:30:00Z"
  }
}
```

### Common Error Codes
- `INVALID_SYMBOL`: Stock symbol doesn't exist
- `CACHE_NOT_FOUND`: Requested cache file not available
- `ANALYSIS_PENDING`: Data still being processed
- `CONFIG_ERROR`: Invalid configuration value

## Data Flow Architecture

### 1. Data Sources
- **Existing Cache Files**: `cache/*.json`
- **Reports**: `reports/**/*.json`
- **Configuration**: `config/config.json`
- **Live Analysis**: Direct module calls

### 2. API Processing
- **Data Aggregation**: Combine multiple sources
- **Real-time Validation**: Check data freshness
- **Error Handling**: Graceful degradation
- **Caching**: 30-second cache for frequent requests

### 3. Frontend Consumption
- **Chart.js Integration**: Direct JSON to charts
- **Auto-refresh**: 30-second polling
- **Error Handling**: User-friendly messages
- **Loading States**: Progress indicators

## Implementation Notes

### Performance Optimizations
- **In-memory caching**: 30-second TTL
- **Lazy loading**: Load data on demand
- **Batch requests**: Combine multiple API calls
- **Compression**: Gzip for large responses

### Security
- **Local-only**: Bind to 127.0.0.1
- **No authentication**: Running locally
- **Read-only**: No data modification endpoints
- **Input validation**: Sanitize all parameters

### Testing
- **Health check**: `GET /api/health`
- **Data validation**: Verify JSON structure
- **Performance**: Response time < 500ms
- **Error handling**: Graceful degradation