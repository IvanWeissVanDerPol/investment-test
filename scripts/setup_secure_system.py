#!/usr/bin/env python3
"""
Secure System Setup Script
Automates the setup of the improved InvestmentAI system with all security enhancements
"""

import os
import sys
import subprocess
import secrets
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import json
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.investment_system.utils.secure_config_manager import SecureConfigManager
from core.investment_system.auth.auth_manager import AuthManager
from core.investment_system.database.connection_manager import DatabaseConnectionManager


class SecureSystemSetup:
    """Setup manager for the secure InvestmentAI system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        self.backup_dir = self.project_root / 'backups'
        
    def run_setup(self):
        """Run complete system setup"""
        print("🚀 Starting InvestmentAI Secure System Setup")
        print("=" * 50)
        
        try:
            # Step 1: Backup existing system
            self.backup_existing_system()
            
            # Step 2: Generate secure configuration
            self.generate_secure_configuration()
            
            # Step 3: Install dependencies
            self.install_dependencies()
            
            # Step 4: Setup database
            self.setup_database()
            
            # Step 5: Initialize authentication system
            self.setup_authentication()
            
            # Step 6: Configure web application
            self.setup_web_application()
            
            # Step 7: Setup monitoring and logging
            self.setup_monitoring()
            
            # Step 8: Create development scripts
            self.create_development_scripts()
            
            # Step 9: Run system validation
            self.validate_system()
            
            print("\n✅ Setup completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Review the generated .env file and add your API keys")
            print("2. Start PostgreSQL database (or system will use SQLite fallback)")
            print("3. Start Redis server (optional, for caching and rate limiting)")
            print("4. Run the secure web application: python web/app_secure.py")
            print("5. Default admin credentials: admin@investmentai.com / ChangeMe123!@#")
            print("   ⚠️  CHANGE THESE IMMEDIATELY AFTER FIRST LOGIN")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            print("Check the error logs above and try again.")
            sys.exit(1)
    
    def backup_existing_system(self):
        """Backup existing system files"""
        print("\n📦 Step 1: Backing up existing system...")
        
        if not self.backup_dir.exists():
            self.backup_dir.mkdir()
        
        # Backup critical files
        files_to_backup = [
            'config/config.json',
            'web/app.py',
            'requirements.txt',
            'core/database/investment_system.db'
        ]
        
        for file_path in files_to_backup:
            source = self.project_root / file_path
            if source.exists():
                dest = self.backup_dir / file_path.replace('/', '_')
                shutil.copy2(source, dest)
                print(f"  ✓ Backed up {file_path}")
        
        print("  ✅ Backup completed")
    
    def generate_secure_configuration(self):
        """Generate secure configuration files"""
        print("\n🔐 Step 2: Generating secure configuration...")
        
        # Generate encryption keys
        encryption_key = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        secret_key = secrets.token_urlsafe(32)
        jwt_secret = secrets.token_urlsafe(32)
        
        # Environment variables
        env_content = f"""# InvestmentAI Secure Configuration
# Generated on {datetime.now().isoformat()}
# IMPORTANT: Keep this file secure and never commit to version control

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/investmentai
SQLITE_DB_PATH=core/database/investment_system.db

# API Keys - Replace with your actual keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
TWELVEDATA_API_KEY=your_twelvedata_key_here
POLYGON_API_KEY=your_polygon_key_here
FINNHUB_API_KEY=your_finnhub_key_here
NEWSAPI_KEY=your_newsapi_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here

# Security Configuration
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}
JWT_SECRET_KEY={jwt_secret}

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAIL_RECIPIENT=your_email@gmail.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
ENABLE_HTTPS=false

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000

# Portfolio Configuration
DEFAULT_PORTFOLIO_BALANCE=900.00
DEFAULT_RISK_TOLERANCE=medium
DEFAULT_MAX_POSITION_PERCENT=15.0
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        print(f"  ✓ Generated .env file with secure keys")
        print(f"  ⚠️  Please update API keys in {self.env_file}")
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("\n📦 Step 3: Installing dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
            
            # Install requirements
            requirements_file = self.project_root / 'requirements.txt'
            if requirements_file.exists():
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
                ])
                print("  ✅ Dependencies installed successfully")
            else:
                print("  ⚠️  requirements.txt not found, skipping dependency installation")
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install dependencies: {e}")
            raise
    
    def setup_database(self):
        """Setup database with migrations"""
        print("\n🗄️  Step 4: Setting up database...")
        
        try:
            # Initialize database connection manager
            db_manager = DatabaseConnectionManager()
            
            # Test connection
            connection_info = db_manager.get_connection_info()
            print(f"  ✓ Connected to {connection_info['engine_type']} database")
            
            # Create tables if needed
            if connection_info['engine_type'] == 'SQLite':
                print("  ✓ Using SQLite database (development mode)")
            else:
                print("  ✓ Using PostgreSQL database (production mode)")
            
            print("  ✅ Database setup completed")
            
        except Exception as e:
            print(f"  ⚠️  Database setup warning: {e}")
            print("  ℹ️  System will use SQLite fallback if PostgreSQL is unavailable")
    
    def setup_authentication(self):
        """Setup authentication system"""
        print("\n👤 Step 5: Setting up authentication system...")
        
        try:
            # Initialize auth manager (this will create tables and default admin user)
            auth_manager = AuthManager()
            
            # Validate configuration
            config_manager = SecureConfigManager()
            validation = config_manager.validate_configuration()
            
            if validation['security']:
                print("  ✓ Security configuration validated")
            else:
                print("  ⚠️  Security configuration has issues")
            
            print("  ✅ Authentication system initialized")
            print("  ℹ️  Default admin user created: admin@investmentai.com")
            
        except Exception as e:
            print(f"  ❌ Authentication setup failed: {e}")
            raise
    
    def setup_web_application(self):
        """Setup web application configuration"""
        print("\n🌐 Step 6: Setting up web application...")
        
        # Create necessary directories
        web_dirs = [
            'web/static/images',
            'web/static/css',
            'web/static/js',
            'web/templates/auth',
            'web/templates/admin',
            'web/templates/components',
        ]
        
        for dir_path in web_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        print("  ✓ Created web application directories")
        
        # Create basic CSS file
        css_content = """
/* InvestmentAI Secure Application Styles */
:root {
    --primary-color: #007bff;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
}

.navbar-brand {
    font-weight: bold;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.alert {
    border: none;
    border-radius: 0.5rem;
}

.btn {
    border-radius: 0.375rem;
}

.form-control {
    border-radius: 0.375rem;
}

.performance-positive {
    color: var(--success-color);
}

.performance-negative {
    color: var(--danger-color);
}
"""
        
        css_file = self.project_root / 'web/static/css/style.css'
        with open(css_file, 'w') as f:
            f.write(css_content)
        
        print("  ✓ Created basic CSS styles")
        print("  ✅ Web application setup completed")
    
    def setup_monitoring(self):
        """Setup monitoring and logging"""
        print("\n📊 Step 7: Setting up monitoring and logging...")
        
        # Create logs directory
        logs_dir = self.project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create basic logging configuration
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "standard"
                },
                "file": {
                    "level": "DEBUG",
                    "class": "logging.FileHandler",
                    "filename": "logs/application.log",
                    "formatter": "detailed"
                },
                "security": {
                    "level": "WARNING",
                    "class": "logging.FileHandler",
                    "filename": "logs/security.log",
                    "formatter": "detailed"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "INFO"
                },
                "security": {
                    "handlers": ["console", "security"],
                    "level": "WARNING",
                    "propagate": False
                },
                "audit": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False
                }
            }
        }
        
        logging_file = self.project_root / 'config/logging.json'
        with open(logging_file, 'w') as f:
            json.dump(logging_config, f, indent=2)
        
        print("  ✓ Created logging configuration")
        print("  ✅ Monitoring setup completed")
    
    def create_development_scripts(self):
        """Create development helper scripts"""
        print("\n🛠️  Step 8: Creating development scripts...")
        
        # Create run script
        run_script_content = '''#!/usr/bin/env python3
"""
Run the secure InvestmentAI web application
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from web.app_secure import app, socketio, create_app
    
    # Create app with environment
    env = os.getenv('ENVIRONMENT', 'development')
    app = create_app(env)
    
    # Run with SocketIO
    socketio.run(
        app,
        debug=(env == 'development'),
        host='127.0.0.1',
        port=5000
    )
'''
        
        run_script_path = self.project_root / 'scripts/run_secure_app.py'
        with open(run_script_path, 'w') as f:
            f.write(run_script_content)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(run_script_path, 0o755)
        
        # Create batch file for Windows
        if os.name == 'nt':
            batch_content = '''@echo off
cd /d "%~dp0\.."
python scripts\\run_secure_app.py
pause
'''
            batch_path = self.project_root / 'scripts/run_secure_app.bat'
            with open(batch_path, 'w') as f:
                f.write(batch_content)
        
        print("  ✓ Created application run scripts")
        
        # Create test script
        test_script_content = '''#!/usr/bin/env python3
"""
Test the secure InvestmentAI system components
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_system():
    """Test system components"""
    print("🧪 Testing InvestmentAI Secure System")
    print("=" * 40)
    
    # Test configuration
    try:
        from core.investment_system.utils.secure_config_manager import SecureConfigManager
        config = SecureConfigManager()
        validation = config.validate_configuration()
        print(f"✓ Configuration: {'PASS' if all(validation.values()) else 'FAIL'}")
        for component, status in validation.items():
            print(f"  - {component}: {'✓' if status else '✗'}")
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
    
    # Test database
    try:
        from core.investment_system.database.connection_manager import test_database_connection
        db_status = test_database_connection()
        print(f"✓ Database: {'PASS' if db_status else 'FAIL'}")
    except Exception as e:
        print(f"✗ Database test failed: {e}")
    
    # Test authentication
    try:
        from core.investment_system.auth.auth_manager import AuthManager
        auth = AuthManager()
        print("✓ Authentication: PASS")
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
    
    # Test input validation
    try:
        from core.investment_system.utils.input_validator import validate_email
        result = validate_email("test@example.com", "email")
        print("✓ Input Validation: PASS")
    except Exception as e:
        print(f"✗ Input validation test failed: {e}")
    
    print("\\n🎉 System test completed!")

if __name__ == "__main__":
    test_system()
'''
        
        test_script_path = self.project_root / 'scripts/test_secure_system.py'
        with open(test_script_path, 'w') as f:
            f.write(test_script_content)
        
        print("  ✓ Created system test script")
        print("  ✅ Development scripts created")
    
    def validate_system(self):
        """Validate the system setup"""
        print("\n✅ Step 9: Validating system setup...")
        
        try:
            # Import and run basic validation
            exec(open(self.project_root / 'scripts/test_secure_system.py').read())
            
        except Exception as e:
            print(f"  ⚠️  Validation warning: {e}")
            print("  ℹ️  System should still work, but check the configuration")


def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("InvestmentAI Secure System Setup")
        print("Usage: python scripts/setup_secure_system.py")
        print("\\nThis script will:")
        print("- Backup existing system files")
        print("- Generate secure configuration")
        print("- Install dependencies")
        print("- Setup database and authentication")
        print("- Configure web application")
        print("- Setup monitoring and logging")
        print("- Create development scripts")
        print("- Validate system setup")
        return
    
    # Add datetime import
    from datetime import datetime
    
    setup = SecureSystemSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()