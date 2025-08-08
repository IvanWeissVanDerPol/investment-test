# Investment Dashboard Web Application

A modern, responsive web dashboard for visualizing AI/Robotics investment portfolio data.

## Features

- **Real-time Portfolio Tracking**: Monitor your AI/Robotics investments
- **Interactive Charts**: Visualize performance with Chart.js
- **Stock Analysis**: Detailed analysis for individual stocks
- **Alert System**: Get notified of important events
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Settings Management**: Configure your preferences

## Quick Start

1. **Install Dependencies**
   ```bash
   cd web
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Dashboard**
   Open your browser to `http://localhost:5000`

## Project Structure

```
web/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── src/
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── utils/           # Helper utilities
│   └── api/             # API endpoints
├── static/
│   ├── css/
│   │   ├── style.css    # Main stylesheet
│   │   └── components/  # Component-specific styles
│   ├── js/
│   │   ├── main.js      # Main JavaScript
│   │   ├── components/  # Component scripts
│   │   └── services/    # API services
│   └── images/          # Icons and assets
├── templates/
│   ├── layouts/
│   │   └── base.html    # Base template
│   ├── pages/           # Page templates
│   │   ├── dashboard.html
│   │   ├── portfolio.html
│   │   ├── stocks.html
│   │   ├── stock_detail.html
│   │   ├── alerts.html
│   │   └── settings.html
│   └── components/      # Reusable components
```

## API Endpoints

### Portfolio
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/portfolio/holdings` - Get individual holdings
- `POST /api/portfolio/update` - Update portfolio

### Stocks
- `GET /api/stocks` - Get all tracked stocks
- `GET /api/stock/<symbol>` - Get stock details
- `GET /api/stock/<symbol>/analysis` - Get analysis data

### Alerts
- `GET /api/alerts` - Get all alerts
- `GET /api/alerts/recent` - Get recent alerts
- `POST /api/alerts/mark-read` - Mark alerts as read

### Settings
- `GET /api/settings` - Get user settings
- `POST /api/settings` - Save user settings

## Configuration

### Environment Variables
Create a `.env` file in the web directory:

```bash
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///investment_dashboard.db
ALPHA_VANTAGE_API_KEY=your-api-key
NEWS_API_KEY=your-news-api-key
```

### Database Setup
The application uses SQLite by default. The database will be created automatically on first run.

## Development

### Running in Development Mode
```bash
python app.py
```

### Code Style
- Follow PEP 8 for Python code
- Use consistent indentation (4 spaces)
- Add docstrings for functions and classes

### Adding New Features
1. Create the route in `app.py`
2. Add the template in `templates/pages/`
3. Add any necessary CSS in `static/css/`
4. Add JavaScript functionality in `static/js/`

## Deployment

### Production Setup
1. Set `FLASK_ENV=production`
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```
3. Configure a reverse proxy (nginx recommended)

### Docker Deployment
```bash
docker build -t investment-dashboard .
docker run -p 5000:5000 investment-dashboard
```

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Mobile Support

The dashboard is fully responsive and works on:
- iOS Safari 13+
- Android Chrome 80+
- Mobile Firefox 75+

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -i :5000
   kill -9 [PID]
   ```

2. **Database connection error**
   - Check that the database file exists
   - Verify database permissions

3. **API key issues**
   - Verify your API keys in the `.env` file
   - Check API rate limits

### Debug Mode
Enable debug mode by setting `FLASK_DEBUG=True` in your `.env` file.

#### Advanced Browser Debugging
The dashboard includes comprehensive browser debugging tools:

**Console Commands:**
```javascript
debugger.help()          // Show all debug commands
debugger.testApi('/api/portfolio/summary')  // Test API endpoints
debugger.performance()   // View performance metrics
debugger.export()        // Export debug logs to JSON
```

**Debug Panel Features:**
- **Toggle Debug Mode**: Click "Debug Mode" in the footer
- **5 Tab Interface**: Logs, API Calls, Errors, Performance, Storage
- **Real-time Updates**: All data updates as you use the dashboard
- **Export Function**: Download debug logs as JSON file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Investment Analysis System and follows the same license terms.