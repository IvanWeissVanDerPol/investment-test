from flask import Blueprint, jsonify, request
import logging
import time
from datetime import datetime
import psutil
import os
import sqlite3
from pathlib import Path

# Create debug API blueprint
debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')

class DebugLogger:
    def __init__(self):
        self.logs = []
        self.api_calls = []
        self.errors = []
        self.start_time = time.time()
    
    def log(self, message, level='info'):
        entry = {
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'process_time': time.time() - self.start_time
        }
        self.logs.append(entry)
        return entry

debug_logger = DebugLogger()

@debug_bp.route('/health')
def health_check():
    """Detailed health check for the dashboard."""
    try:
        # Check database connection
        db_path = Path('../core/database/investment_system.db')
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Test database queries
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_counts = {}
        for table in tables:
            table_name = table[0]
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            table_counts[table_name] = count
        
        conn.close()
        
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - debug_logger.start_time,
            'database': {
                'connected': True,
                'tables': table_counts,
                'path': str(db_path)
            },
            'system': {
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'cpu_percent': psutil.cpu_percent(interval=1)
            },
            'api': {
                'endpoint': '/api/debug/health',
                'response_time': f"{time.time() - debug_logger.start_time:.3f}s"
            }
        }
        
        debug_logger.log('Health check completed successfully')
        return jsonify(health_data)
        
    except Exception as e:
        debug_logger.log(f'Health check failed: {str(e)}', 'error')
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@debug_bp.route('/logs')
def get_logs():
    """Get application logs."""
    return jsonify({
        'logs': debug_logger.logs,
        'api_calls': debug_logger.api_calls,
        'errors': debug_logger.errors,
        'timestamp': datetime.now().isoformat()
    })

@debug_bp.route('/test-endpoint')
def test_endpoint():
    """Test any API endpoint."""
    endpoint = request.args.get('endpoint', '/api/portfolio')
    
    try:
        # Simulate endpoint testing
        start_time = time.time()
        
        # Test database connection
        db_path = Path('../core/database/investment_system.db')
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        if 'portfolio' in endpoint:
            result = conn.execute('SELECT * FROM portfolio_summary ORDER BY date DESC LIMIT 1').fetchone()
        elif 'stocks' in endpoint:
            result = conn.execute('SELECT * FROM stocks LIMIT 5').fetchall()
        elif 'positions' in endpoint:
            result = conn.execute('SELECT * FROM positions LIMIT 5').fetchall()
        else:
            result = {'test': 'endpoint'}
        
        conn.close()
        
        duration = time.time() - start_time
        
        return jsonify({
            'endpoint': endpoint,
            'status': 'success',
            'duration': f"{duration:.3f}s",
            'result': dict(result) if result else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'endpoint': endpoint,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@debug_bp.route('/system-info')
def system_info():
    """Get detailed system information."""
    try:
        # Database file info
        db_path = Path('../core/database/investment_system.db')
        db_stats = {
            'exists': db_path.exists(),
            'size': db_path.stat().st_size if db_path.exists() else 0,
            'last_modified': datetime.fromtimestamp(db_path.stat().st_mtime).isoformat() if db_path.exists() else None
        }
        
        # Python environment
        import sys
        python_info = {
            'version': sys.version,
            'executable': sys.executable,
            'platform': sys.platform
        }
        
        # Flask app info
        from flask import current_app
        app_info = {
            'debug': current_app.debug,
            'testing': current_app.testing,
            'config': {k: str(v) for k, v in current_app.config.items() if not k.startswith('_')}
        }
        
        return jsonify({
            'database': db_stats,
            'python': python_info,
            'flask': app_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@debug_bp.route('/performance')
def performance_metrics():
    """Get performance metrics."""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Database performance test
        db_path = Path('../core/database/investment_system.db')
        conn = sqlite3.connect(str(db_path))
        
        # Test query performance
        queries = [
            ('SELECT COUNT(*) FROM portfolio_summary', 'portfolio_count'),
            ('SELECT COUNT(*) FROM stocks', 'stocks_count'),
            ('SELECT COUNT(*) FROM positions', 'positions_count'),
            ('SELECT AVG(current_price) FROM stocks', 'avg_price')
        ]
        
        query_times = {}
        for query, name in queries:
            start = time.time()
            result = conn.execute(query).fetchone()[0]
            duration = time.time() - start
            query_times[name] = {
                'result': result,
                'duration': f"{duration:.4f}s"
            }
        
        conn.close()
        
        return jsonify({
            'memory': {
                'total_gb': memory.total / (1024**3),
                'used_gb': memory.used / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent': memory.percent
            },
            'cpu_percent': cpu_percent,
            'disk': {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': (disk.used / disk.total) * 100
            },
            'database_queries': query_times,
            'uptime': time.time() - debug_logger.start_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@debug_bp.route('/simulate-error')
def simulate_error():
    """Simulate different types of errors for testing."""
    error_type = request.args.get('type', 'database')
    
    try:
        if error_type == 'database':
            # Simulate database error
            conn = sqlite3.connect('/invalid/path/to/database.db')
            conn.execute('SELECT * FROM nonexistent_table')
        elif error_type == 'api':
            # Simulate API error
            raise ValueError("API endpoint not found")
        elif error_type == 'validation':
            # Simulate validation error
            raise ValueError("Invalid input data")
        else:
            raise ValueError(f"Unknown error type: {error_type}")
            
    except Exception as e:
        debug_logger.log(f'Simulated error: {str(e)}', 'error')
        return jsonify({
            'error': str(e),
            'error_type': error_type,
            'timestamp': datetime.now().isoformat()
        }), 500

# Add debug logging to all API calls
@debug_bp.before_request
def log_request():
    debug_logger.log(f'Request: {request.method} {request.path}', 'info', {
        'method': request.method,
        'path': request.path,
        'args': dict(request.args),
        'remote_addr': request.remote_addr
    })

@debug_bp.after_request
def log_response(response):
    debug_logger.log(f'Response: {request.path} - {response.status_code}', 'info' if response.status_code < 400 else 'error', {
        'path': request.path,
        'status_code': response.status_code,
        'content_length': response.content_length
    })
    return response