"""
Secure Investment Dashboard Web Application
Enhanced version with authentication, security, and real-time features
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

# Add the core investment system to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our secure modules
from core.investment_system.auth import AuthManager, login_required, admin_required, get_auth_manager
from core.investment_system.utils.secure_config_manager import get_config_manager
from core.investment_system.utils.input_validator import get_validator, ValidationError, validate_string, validate_email
from core.investment_system.monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel
from core.investment_system.database.connection_manager import get_connection_manager

# Import existing modules (updated imports)
from src.services.database_service import DatabaseService
from src.utils.formatters import format_currency, format_percentage, get_performance_color

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with security
app = Flask(__name__)

# Load configuration
config_manager = get_config_manager()
security_config = config_manager.get_security_config()

app.config.update({
    'SECRET_KEY': security_config.secret_key,
    'SESSION_COOKIE_SECURE': security_config.enable_https,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(seconds=security_config.session_timeout),
    'WTF_CSRF_ENABLED': True,
    'WTF_CSRF_TIME_LIMIT': 3600,
})

# Initialize extensions
CORS(app, origins=['http://localhost:5000'])  # Restrict CORS
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:5000'])

# Initialize managers
auth_manager = get_auth_manager()
audit_logger = get_audit_logger()
validator = get_validator()
db_manager = get_connection_manager()

# Configuration
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent / "core" / "database" / "investment_system.db"

# Initialize services
db_service = DatabaseService(str(DB_PATH))


# Request hooks for security and auditing
@app.before_request
def before_request():
    """Security checks and request initialization"""
    
    # Generate request ID for audit trail
    request.id = f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(request.url) % 10000}"
    
    # Check for suspicious patterns
    user_agent = request.user_agent.string or ""
    if any(pattern in user_agent.lower() for pattern in ['sqlmap', 'nikto', 'nessus', 'burp']):
        audit_logger.log_event(
            EventType.SECURITY_VIOLATION,
            SeverityLevel.HIGH,
            resource=request.endpoint,
            details={'reason': 'suspicious_user_agent', 'user_agent': user_agent}
        )
        return jsonify({'error': 'Request blocked'}), 403
    
    # Rate limiting check (basic)
    ip_address = request.remote_addr
    if _is_rate_limited(ip_address):
        audit_logger.log_event(
            EventType.RATE_LIMIT_EXCEEDED,
            SeverityLevel.MEDIUM,
            details={'ip_address': ip_address, 'endpoint': request.endpoint}
        )
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    # Load user from session if authenticated
    jwt_token = session.get('jwt_token')
    if jwt_token:
        user = auth_manager.verify_session(jwt_token)
        if user:
            g.current_user = user
            g.session_id = session.get('session_id')


def _is_rate_limited(ip_address: str) -> bool:
    """Basic rate limiting check (implement proper Redis-based limiting in production)"""
    # For now, just return False - implement proper rate limiting with Redis
    return False


@app.after_request
def after_request(response):
    """Security headers and response processing"""
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    if security_config.enable_https:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' ws: wss:; "
        "object-src 'none'; "
        "base-uri 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and processing"""
    
    if request.method == 'POST':
        try:
            # Validate input
            email_or_username = validate_string(
                request.form.get('email_or_username', ''),
                'email_or_username',
                min_length=3,
                max_length=100
            )
            password = request.form.get('password', '')
            
            if not password:
                raise ValidationError('password', 'Password is required')
            
            # Authenticate user
            auth_result = auth_manager.authenticate_user(
                email_or_username,
                password,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            if auth_result:
                # Set session
                session['jwt_token'] = auth_result['session']['jwt_token']
                session['session_id'] = auth_result['session']['session_id']
                session['user_id'] = auth_result['user']['user_id']
                session.permanent = True
                
                # Audit log
                audit_logger.log_event(
                    EventType.LOGIN_SUCCESS,
                    SeverityLevel.LOW,
                    user_id=auth_result['user']['user_id'],
                    details={'login_method': 'password'}
                )
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Audit log failed attempt
                audit_logger.log_event(
                    EventType.LOGIN_FAILURE,
                    SeverityLevel.MEDIUM,
                    details={'email_or_username': email_or_username[:20] + '***'}
                )
                
                flash('Invalid credentials or account locked', 'error')
                
        except ValidationError as e:
            flash(f'Invalid input: {e.message}', 'error')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed due to system error', 'error')
    
    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    """User logout"""
    
    user_id = session.get('user_id')
    jwt_token = session.get('jwt_token')
    
    if jwt_token:
        auth_manager.logout_user(jwt_token)
    
    # Clear session
    session.clear()
    
    # Audit log
    audit_logger.log_event(
        EventType.LOGOUT,
        SeverityLevel.LOW,
        user_id=user_id
    )
    
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    
    if request.method == 'POST':
        try:
            # Validate input
            email = validate_email(request.form.get('email', ''), 'email')
            username = validate_string(request.form.get('username', ''), 'username', min_length=3, max_length=30)
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            first_name = validate_string(request.form.get('first_name', ''), 'first_name', required=False, max_length=50)
            last_name = validate_string(request.form.get('last_name', ''), 'last_name', required=False, max_length=50)
            
            # Validate password
            if password != confirm_password:
                raise ValidationError('password', 'Passwords do not match')
            
            password_validation = auth_manager.security.validate_password_strength(password)
            if not password_validation['is_valid']:
                raise ValidationError('password', f"Password too weak: {', '.join(password_validation['issues'])}")
            
            # Create user
            user = auth_manager.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Audit log
            audit_logger.log_event(
                EventType.LOGIN_SUCCESS,  # User creation is a form of initial login
                SeverityLevel.LOW,
                user_id=user.user_id,
                details={'registration': True, 'email': email}
            )
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except ValidationError as e:
            flash(f'Registration failed: {e.message}', 'error')
        except ValueError as e:
            flash(f'Registration failed: {str(e)}', 'error')
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('Registration failed due to system error', 'error')
    
    return render_template('auth/register.html')


# Context processors for templates
@app.context_processor
def utility_processor():
    """Add utility functions to all templates."""
    return {
        'format_currency': format_currency,
        'format_percentage': format_percentage,
        'get_performance_color': get_performance_color,
        'now': datetime.now(),
        'current_user': getattr(g, 'current_user', None)
    }


# Secure main routes
@app.route('/')
@login_required
def dashboard():
    """Main dashboard with portfolio overview."""
    
    # Audit log page access
    audit_logger.log_event(
        EventType.PORTFOLIO_VIEWED,
        SeverityLevel.LOW,
        resource='dashboard'
    )
    
    try:
        portfolio = db_service.get_portfolio_summary()
        positions = db_service.get_positions()
        alerts = db_service.get_alerts(5)
        sectors = db_service.get_sector_allocations()
        
        return render_template('pages/dashboard.html',
                             portfolio=portfolio,
                             positions=positions,
                             alerts=alerts,
                             sectors=sectors)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard data', 'error')
        return render_template('pages/error.html'), 500


@app.route('/portfolio')
@login_required
def portfolio():
    """Detailed portfolio view."""
    
    audit_logger.log_event(
        EventType.PORTFOLIO_VIEWED,
        SeverityLevel.LOW,
        resource='portfolio'
    )
    
    try:
        positions = db_service.get_positions()
        history = db_service.get_portfolio_history(30)
        sectors = db_service.get_sector_allocations()
        
        return render_template('pages/portfolio.html',
                             positions=positions,
                             history=history,
                             sectors=sectors)
    except Exception as e:
        logger.error(f"Portfolio error: {e}")
        flash('Error loading portfolio data', 'error')
        return render_template('pages/error.html'), 500


@app.route('/stocks')
@login_required
def stocks():
    """Stock analysis and research page."""
    
    try:
        stocks_data = db_service.get_stocks()
        return render_template('pages/stocks.html', stocks=stocks_data)
    except Exception as e:
        logger.error(f"Stocks error: {e}")
        flash('Error loading stocks data', 'error')
        return render_template('pages/error.html'), 500


@app.route('/stock/<symbol>')
@login_required
def stock_detail(symbol):
    """Individual stock detail page."""
    
    try:
        # Validate stock symbol
        symbol = validate_string(symbol, 'symbol', pattern=r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$')
        
        stock_data = db_service.get_stock_detail(symbol)
        if not stock_data:
            return render_template('pages/404.html'), 404
        
        return render_template('pages/stock_detail.html',
                             stock=stock_data['stock'],
                             analysis=stock_data['analysis'],
                             prices=stock_data['prices'],
                             news=stock_data['news'])
    except ValidationError as e:
        flash(f'Invalid stock symbol: {e.message}', 'error')
        return redirect(url_for('stocks'))
    except Exception as e:
        logger.error(f"Stock detail error: {e}")
        flash('Error loading stock data', 'error')
        return render_template('pages/error.html'), 500


@app.route('/alerts')
@login_required
def alerts():
    """Alerts and notifications page."""
    
    try:
        alerts_data = db_service.get_alerts(50)
        return render_template('pages/alerts.html', alerts=alerts_data)
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        flash('Error loading alerts data', 'error')
        return render_template('pages/error.html'), 500


@app.route('/settings')
@login_required
def settings():
    """Settings and configuration page."""
    
    return render_template('pages/settings.html')


@app.route('/analytics')
@login_required
def analytics():
    """Advanced analytics page."""
    
    return render_template('pages/analytics.html')


@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin panel"""
    
    audit_logger.log_event(
        EventType.PERMISSION_GRANTED,
        SeverityLevel.MEDIUM,
        resource='admin_panel',
        action='access'
    )
    
    try:
        # Get system stats
        security_summary = audit_logger.get_security_summary(24)
        connection_info = db_manager.get_connection_info()
        
        return render_template('admin/dashboard.html',
                             security_summary=security_summary,
                             connection_info=connection_info)
    except Exception as e:
        logger.error(f"Admin error: {e}")
        flash('Error loading admin data', 'error')
        return render_template('pages/error.html'), 500


# Secure API routes
@app.route('/api/portfolio/summary')
@login_required
def api_portfolio_summary():
    """API endpoint for portfolio summary."""
    
    try:
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
    except Exception as e:
        logger.error(f"API portfolio summary error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/positions')
@login_required
def api_positions():
    """API endpoint for positions data."""
    
    try:
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
    except Exception as e:
        logger.error(f"API positions error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    
    # Verify user is authenticated
    jwt_token = session.get('jwt_token')
    if not jwt_token:
        return False  # Reject connection
    
    user = auth_manager.verify_session(jwt_token)
    if not user:
        return False  # Reject connection
    
    emit('connected', {'status': 'connected', 'user': user.username})
    
    audit_logger.log_event(
        EventType.API_CALL,
        SeverityLevel.LOW,
        user_id=user.user_id,
        resource='websocket',
        action='connect'
    )


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    
    user_id = session.get('user_id')
    if user_id:
        audit_logger.log_event(
            EventType.API_CALL,
            SeverityLevel.LOW,
            user_id=user_id,
            resource='websocket',
            action='disconnect'
        )


@socketio.on('request_portfolio_update')
def handle_portfolio_update():
    """Handle request for portfolio update"""
    
    jwt_token = session.get('jwt_token')
    if not jwt_token:
        return
    
    user = auth_manager.verify_session(jwt_token)
    if not user:
        return
    
    try:
        # Get fresh portfolio data
        portfolio = db_service.get_portfolio_summary()
        positions = db_service.get_positions()
        
        emit('portfolio_update', {
            'portfolio': portfolio.to_dict() if portfolio else {},
            'positions': [pos.to_dict() for pos in positions],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"WebSocket portfolio update error: {e}")
        emit('error', {'message': 'Failed to get portfolio update'})


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('pages/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('pages/500.html'), 500


@app.errorhandler(403)
def forbidden(error):
    audit_logger.log_event(
        EventType.PERMISSION_DENIED,
        SeverityLevel.MEDIUM,
        resource=request.endpoint,
        details={'reason': 'insufficient_permissions'}
    )
    return render_template('pages/403.html'), 403


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


# Application factory function
def create_app(config_name='development'):
    """Application factory function"""
    
    # Additional configuration based on environment
    if config_name == 'production':
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
            'SESSION_COOKIE_SECURE': True,
        })
    elif config_name == 'testing':
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
        })
    
    return app


# Development server
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates/auth', exist_ok=True)
    os.makedirs('templates/admin', exist_ok=True)
    
    # Run with SocketIO support
    socketio.run(
        app,
        debug=config_manager.is_development(),
        host='127.0.0.1',
        port=5000,
        use_reloader=False  # Disable reloader with SocketIO
    )