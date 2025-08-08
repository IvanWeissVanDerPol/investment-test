"""
Investment Dashboard Web Application
A Flask-based web interface for visualizing AI/Robotics investment data.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import os
from pathlib import Path
from datetime import datetime

# Import our organized modules
from src.services.database_service import DatabaseService
from src.utils.formatters import format_currency, format_percentage, get_performance_color

# Initialize Flask app
app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "core" / "database" / "investment_system.db"

# Initialize services
db_service = DatabaseService(str(DB_PATH))

# Context processors for templates
@app.context_processor

def utility_processor():
    """Add utility functions to all templates."""
    return {
        'format_currency': format_currency,
        'format_percentage': format_percentage,
        'get_performance_color': get_performance_color,
        'now': datetime.now()
    }

# Main routes
@app.route('/')
def dashboard():
    """Main dashboard with portfolio overview."""
    portfolio = db_service.get_portfolio_summary()
    positions = db_service.get_positions()
    alerts = db_service.get_alerts(5)
    sectors = db_service.get_sector_allocations()
    
    return render_template('pages/dashboard.html',
                         portfolio=portfolio,
                         positions=positions,
                         alerts=alerts,
                         sectors=sectors)

@app.route('/portfolio')
def portfolio():
    """Detailed portfolio view."""
    positions = db_service.get_positions()
    history = db_service.get_portfolio_history(30)
    sectors = db_service.get_sector_allocations()
    
    return render_template('pages/portfolio.html',
                         positions=positions,
                         history=history,
                         sectors=sectors)

@app.route('/stocks')
def stocks():
    """Stock analysis and research page."""
    stocks_data = db_service.get_stocks()
    
    return render_template('pages/stocks.html',
                         stocks=stocks_data)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """Individual stock detail page."""
    stock_data = db_service.get_stock_detail(symbol)
    if not stock_data:
        return render_template('pages/404.html'), 404
    
    return render_template('pages/stock_detail.html',
                         stock=stock_data['stock'],
                         analysis=stock_data['analysis'],
                         prices=stock_data['prices'],
                         news=stock_data['news'])

@app.route('/alerts')
def alerts():
    """Alerts and notifications page."""
    alerts_data = db_service.get_alerts(50)
    
    return render_template('pages/alerts.html',
                         alerts=alerts_data)

@app.route('/settings')
def settings():
    """Settings and configuration page."""
    return render_template('pages/settings.html')

@app.route('/analytics')
def analytics():
    """Advanced analytics page."""
    return render_template('pages/analytics.html')

# API routes
@app.route('/api/portfolio/summary')
def api_portfolio_summary():
    """API endpoint for portfolio summary."""
    summary = db_service.get_portfolio_summary()
    if summary:
        return jsonify({
            'total_value': summary.total_value,
            'available_cash': summary.available_cash,
            'daily_change': summary.daily_change,
            'daily_change_percent': summary.daily_change_percent,
            'ai_allocation_percent': summary.ai_allocation_percent,
            'green_allocation_percent': summary.green_allocation_percent,
            'last_updated': summary.last_updated.isoformat()
        })
    return jsonify({})

@app.route('/api/positions')
def api_positions():
    """API endpoint for positions data."""
    positions = db_service.get_positions()
    return jsonify([{
        'symbol': pos.symbol,
        'name': pos.name,
        'sector': pos.sector,
        'quantity': pos.quantity,
        'average_cost': pos.average_cost,
        'current_price': pos.current_price,
        'market_value': pos.market_value,
        'unrealized_pnl': pos.unrealized_pnl,
        'unrealized_pnl_percent': pos.unrealized_pnl_percent
    } for pos in positions])

@app.route('/api/stocks')
def api_stocks():
    """API endpoint for stocks data."""
    stocks = db_service.get_stocks()
    return jsonify(stocks)

@app.route('/api/stock/<symbol>')
def api_stock(symbol):
    """API endpoint for individual stock data."""
    stock_data = db_service.get_stock_detail(symbol)
    if not stock_data:
        return jsonify({'error': 'Stock not found'}), 404
    
    return jsonify({
        'stock': stock_data['stock'],
        'analysis': stock_data['analysis'],
        'prices': stock_data['prices'],
        'news': stock_data['news']
    })

@app.route('/api/stock/<symbol>/price')
def api_stock_price(symbol):
    """API endpoint for stock price history."""
    days = request.args.get('days', 30, type=int)
    prices = db_service.get_price_history(symbol, days)
    return jsonify(prices)

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts."""
    alerts = db_service.get_alerts(50)
    return jsonify(alerts)

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """Trigger data synchronization."""
    # In a real app, this would trigger analysis scripts
    return jsonify({
        'status': 'sync_triggered',
        'timestamp': datetime.now().isoformat()
    })

# Static file serving
@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('pages/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('pages/500.html'), 500

# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Jinja2 filter for currency formatting."""
    return format_currency(value)

@app.template_filter('percentage')
def percentage_filter(value):
    """Jinja2 filter for percentage formatting."""
    return format_percentage(value)

@app.template_filter('performance_color')
def performance_color_filter(value):
    """Jinja2 filter for performance color."""
    return get_performance_color(value)

# Configuration
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=5000)