# Local Web Dashboard Architecture

## Overview
A simple Flask-based web dashboard for visualizing investment analysis data locally. Designed to run entirely on your PC with minimal setup and maximum simplicity.

## Technology Stack
- **Backend**: Python Flask (lightweight, local-only)
- **Frontend**: HTML/CSS/JavaScript with Chart.js for visualizations
- **Data Storage**: JSON files and existing cache system
- **Communication**: Simple REST API endpoints

## Project Structure
```
ivan/
├── web_dashboard/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Web dashboard dependencies
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   ├── js/
│   │   │   └── dashboard.js
│   │   └── images/
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── portfolio.html
│   │   ├── analysis.html
│   │   └── settings.html
│   └── data/
│       └── api_endpoints.py   # Simple data endpoints
├── src/investment_system/     # Existing analysis modules
└── cache/                     # Existing data storage
```

## Key Features

### Dashboard Views
1. **Overview Dashboard**
   - Portfolio summary
   - Recent AI decisions
   - Key metrics (balance, daily change, risk score)

2. **Portfolio Analysis**
   - Stock positions with visual charts
   - Risk assessment visualization
   - Performance tracking

3. **Market Intelligence**
   - AI recommendations table
   - Sentiment analysis charts
   - Smart money tracking

4. **Settings & Configuration**
   - Portfolio parameters
   - Alert thresholds
   - API key management

## Simple API Design

### Endpoints
```
GET /api/portfolio          # Current portfolio state
GET /api/ai-decisions       # Recent AI recommendations
GET /api/market-data        # Real-time market data
GET /api/sentiment          # Sentiment analysis results
GET /api/risk-metrics       # Risk assessment data
POST /api/settings          # Update configuration
GET /api/cache/<filename>   # Access cached data
```

### Data Flow
1. **Existing Analysis** → **JSON Cache** → **Flask API** → **Frontend Charts**
2. **Real-time Updates** → **Simple Polling** → **Auto-refresh Dashboard**

## Installation & Setup

### Quick Start
```bash
# Navigate to web dashboard
cd web_dashboard

# Install dependencies
pip install -r requirements.txt

# Start the web server
python app.py

# Open browser to http://localhost:5000
```

### Requirements (web_dashboard/requirements.txt)
```
Flask==2.3.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
```

## Security Considerations
- Local-only access (127.0.0.1)
- No external dependencies beyond Flask
- Read-only access to existing data
- No sensitive data exposure

## Development Phases

### Phase 1: Basic Dashboard (Week 1)
- Simple Flask app with basic endpoints
- Portfolio overview page
- Basic charts with Chart.js

### Phase 2: Enhanced Views (Week 2)
- Individual stock analysis pages
- Interactive charts
- Settings management

### Phase 3: Real-time Updates (Week 3)
- Live data refresh
- Alert notifications
- Advanced visualizations

## Integration Points

### Data Sources
- **Cache Directory**: Existing JSON files with analysis results
- **Reports**: Generated analysis reports
- **Configuration**: config/config.json for user settings

### Existing Modules
- `src.investment_system.analysis.quick_analysis`
- `src.investment_system.portfolio.portfolio_analysis`
- `src.investment_system.monitoring.system_monitor`

## Next Steps
1. Create basic Flask app structure
2. Implement core API endpoints
3. Build dashboard templates
4. Add Chart.js visualizations
5. Test with existing data