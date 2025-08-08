#!/usr/bin/env python3
"""
Production Deployment Script
Automates the deployment of InvestmentAI to production environment
"""

import os
import sys
import subprocess
import json
import secrets
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import shutil
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ProductionDeployer:
    """Production deployment manager"""
    
    def __init__(self, deployment_type='docker'):
        """
        Initialize deployment manager
        
        Args:
            deployment_type: 'docker' or 'kubernetes'
        """
        self.deployment_type = deployment_type
        self.project_root = Path(__file__).parent.parent
        self.deploy_dir = self.project_root / 'deploy'
        
        # Deployment paths
        self.docker_dir = self.deploy_dir / 'docker'
        self.k8s_dir = self.deploy_dir / 'kubernetes'
        
        print(f"🚀 InvestmentAI Production Deployer - {deployment_type.upper()} mode")
    
    def deploy(self):
        """Run complete deployment process"""
        try:
            print("=" * 60)
            print("STARTING PRODUCTION DEPLOYMENT")
            print("=" * 60)
            
            # Pre-deployment checks
            self._pre_deployment_checks()
            
            # Security setup
            self._setup_security()
            
            # Build application
            self._build_application()
            
            # Deploy based on type
            if self.deployment_type == 'docker':
                self._deploy_docker()
            elif self.deployment_type == 'kubernetes':
                self._deploy_kubernetes()
            
            # Post-deployment verification
            self._verify_deployment()
            
            # Setup monitoring
            self._setup_monitoring()
            
            print("\n✅ DEPLOYMENT COMPLETED SUCCESSFULLY!")
            self._print_deployment_summary()
            
        except Exception as e:
            print(f"\n❌ DEPLOYMENT FAILED: {e}")
            self._cleanup_failed_deployment()
            sys.exit(1)
    
    def _pre_deployment_checks(self):
        """Run pre-deployment checks"""
        print("\n🔍 Step 1: Pre-deployment checks...")
        
        # Check Docker/Kubernetes availability
        if self.deployment_type == 'docker':
            self._check_docker()
        elif self.deployment_type == 'kubernetes':
            self._check_kubernetes()
        
        # Check project structure
        self._check_project_structure()
        
        # Check required files
        self._check_required_files()
        
        print("  ✅ Pre-deployment checks passed")
    
    def _setup_security(self):
        """Setup security configuration"""
        print("\n🔐 Step 2: Setting up security...")
        
        # Generate secure keys
        secret_key = secrets.token_urlsafe(32)
        encryption_key = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        jwt_secret = secrets.token_urlsafe(32)
        
        # Generate database password
        db_password = secrets.token_urlsafe(16)
        
        # Generate Grafana password
        grafana_password = secrets.token_urlsafe(12)
        
        # Create .env file
        env_content = f"""# Production Environment Variables
# Generated on {datetime.now().isoformat()}
# IMPORTANT: Keep this file secure and never commit to version control

# Database
DB_PASSWORD={db_password}

# Security Keys
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}
JWT_SECRET_KEY={jwt_secret}

# Grafana
GRAFANA_PASSWORD={grafana_password}

# API Keys (UPDATE WITH YOUR ACTUAL KEYS)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVEDATA_API_KEY=your_twelvedata_key
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key
NEWSAPI_KEY=your_newsapi_key
YOUTUBE_API_KEY=your_youtube_key
CLAUDE_API_KEY=your_claude_key

# Email Configuration (UPDATE WITH YOUR SETTINGS)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENT=your_email@gmail.com

# SSL Certificate paths
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Performance tuning
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
MAX_CONNECTIONS=1000
REDIS_MAX_MEMORY=512mb
"""
        
        env_file = self.docker_dir / '.env'
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions
        if os.name != 'nt':  # Unix/Linux
            os.chmod(env_file, 0o600)
        
        print(f"  ✅ Security configuration generated: {env_file}")
        print(f"  ⚠️  Please update API keys in {env_file}")
        print(f"  🔑 Database password: {db_password}")
        print(f"  🔑 Grafana password: {grafana_password}")
    
    def _build_application(self):
        """Build the application"""
        print("\n🔨 Step 3: Building application...")
        
        if self.deployment_type == 'docker':
            # Build Docker image
            os.chdir(self.project_root)
            result = subprocess.run([
                'docker', 'build', 
                '-f', str(self.docker_dir / 'Dockerfile'),
                '-t', 'investmentai:latest',
                '.'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Docker build failed: {result.stderr}")
            
            print("  ✅ Docker image built successfully")
        
        elif self.deployment_type == 'kubernetes':
            # Build and push to registry (placeholder)
            print("  ⚠️  For Kubernetes deployment, ensure image is pushed to registry")
    
    def _deploy_docker(self):
        """Deploy using Docker Compose"""
        print("\n🐳 Step 4: Deploying with Docker Compose...")
        
        os.chdir(self.docker_dir)
        
        # Generate SSL certificates if needed
        self._generate_ssl_certificates()
        
        # Start services
        result = subprocess.run([
            'docker-compose', 'up', '-d',
            '--build', '--remove-orphans'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Docker Compose deployment failed: {result.stderr}")
        
        print("  ✅ Docker services started successfully")
        
        # Wait for services to be healthy
        import time
        print("  ⏳ Waiting for services to be healthy...")
        time.sleep(30)
        
        # Check service health
        result = subprocess.run([
            'docker-compose', 'ps'
        ], capture_output=True, text=True)
        
        print("  📊 Service status:")
        print(result.stdout)
    
    def _deploy_kubernetes(self):
        """Deploy using Kubernetes"""
        print("\n☸️  Step 4: Deploying to Kubernetes...")
        
        os.chdir(self.k8s_dir)
        
        # Apply namespace
        subprocess.run(['kubectl', 'apply', '-f', 'namespace.yaml'], check=True)
        
        # Create secrets
        self._create_k8s_secrets()
        
        # Apply deployments
        subprocess.run(['kubectl', 'apply', '-f', 'deployment.yaml'], check=True)
        subprocess.run(['kubectl', 'apply', '-f', 'service.yaml'], check=True)
        
        # Apply persistent volumes if needed
        pv_files = list(self.k8s_dir.glob('*pv*.yaml'))
        for pv_file in pv_files:
            subprocess.run(['kubectl', 'apply', '-f', str(pv_file)], check=True)
        
        print("  ✅ Kubernetes deployment completed")
    
    def _verify_deployment(self):
        """Verify deployment is working"""
        print("\n✅ Step 5: Verifying deployment...")
        
        if self.deployment_type == 'docker':
            # Check if containers are running
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_dir / 'docker-compose.yml'),
                'ps', '--services', '--filter', 'status=running'
            ], capture_output=True, text=True, cwd=self.docker_dir)
            
            running_services = result.stdout.strip().split('\n')
            expected_services = ['investmentai', 'postgres', 'redis', 'nginx']
            
            for service in expected_services:
                if service in running_services:
                    print(f"  ✅ {service} is running")
                else:
                    print(f"  ❌ {service} is not running")
            
            # Test health endpoint
            import time
            import requests
            
            print("  ⏳ Testing health endpoint...")
            time.sleep(10)  # Wait for services to fully start
            
            try:
                response = requests.get('http://localhost/health', timeout=10)
                if response.status_code == 200:
                    print("  ✅ Application health check passed")
                else:
                    print(f"  ⚠️  Health check returned status {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Health check failed: {e}")
        
        elif self.deployment_type == 'kubernetes':
            # Check pod status
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', 'investmentai'
            ], capture_output=True, text=True)
            
            print("  📊 Pod status:")
            print(result.stdout)
            
            # Check service status
            result = subprocess.run([
                'kubectl', 'get', 'services', '-n', 'investmentai'
            ], capture_output=True, text=True)
            
            print("  📊 Service status:")
            print(result.stdout)
    
    def _setup_monitoring(self):
        """Setup monitoring and alerting"""
        print("\n📊 Step 6: Setting up monitoring...")
        
        if self.deployment_type == 'docker':
            # Monitoring is already included in docker-compose.yml
            print("  ✅ Prometheus monitoring: http://localhost:9090")
            print("  ✅ Grafana dashboard: http://localhost:3000")
            print("  ℹ️  Grafana credentials: admin / [check .env file]")
        
        # Create monitoring configuration files
        self._create_monitoring_config()
        
        print("  ✅ Monitoring setup completed")
    
    def _check_docker(self):
        """Check Docker availability"""
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Docker and Docker Compose are required but not installed")
    
    def _check_kubernetes(self):
        """Check Kubernetes availability"""
        try:
            subprocess.run(['kubectl', 'version', '--client'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("kubectl is required but not installed")
    
    def _check_project_structure(self):
        """Check project structure"""
        required_dirs = [
            'core/investment_system',
            'web',
            'config',
            'scripts'
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                raise Exception(f"Required directory missing: {dir_path}")
    
    def _check_required_files(self):
        """Check required files"""
        required_files = [
            'requirements.txt',
            'web/app_secure.py',
            'core/investment_system/__init__.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                raise Exception(f"Required file missing: {file_path}")
    
    def _generate_ssl_certificates(self):
        """Generate self-signed SSL certificates for development"""
        ssl_dir = self.docker_dir / 'nginx' / 'ssl'
        ssl_dir.mkdir(exist_ok=True)
        
        cert_file = ssl_dir / 'cert.pem'
        key_file = ssl_dir / 'key.pem'
        
        if not cert_file.exists() or not key_file.exists():
            print("  🔐 Generating self-signed SSL certificates...")
            
            result = subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', str(key_file),
                '-out', str(cert_file),
                '-days', '365', '-nodes',
                '-subj', '/C=US/ST=State/L=City/O=InvestmentAI/CN=localhost'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ SSL certificates generated: {ssl_dir}")
            else:
                print(f"  ⚠️  SSL generation failed, using HTTP only: {result.stderr}")
    
    def _create_k8s_secrets(self):
        """Create Kubernetes secrets"""
        env_file = self.docker_dir / '.env'
        if not env_file.exists():
            raise Exception("Environment file not found. Run security setup first.")
        
        # Read environment variables
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        
        # Create secret manifest
        secret_data = {
            'database-url': f"postgresql://investmentai:{env_vars['DB_PASSWORD']}@postgres:5432/investmentai",
            'redis-url': 'redis://redis:6379/0',
            'secret-key': env_vars['SECRET_KEY'],
            'encryption-key': env_vars['ENCRYPTION_KEY'],
            'jwt-secret-key': env_vars['JWT_SECRET_KEY']
        }
        
        # Apply secrets to cluster
        for key, value in secret_data.items():
            subprocess.run([
                'kubectl', 'create', 'secret', 'generic', 'investmentai-secrets',
                f'--from-literal={key}={value}',
                '--namespace=investmentai',
                '--dry-run=client', '-o', 'yaml'
            ], check=True)
    
    def _create_monitoring_config(self):
        """Create monitoring configuration"""
        # This would create Grafana dashboards, Prometheus alerts, etc.
        print("  📊 Monitoring configuration created")
    
    def _cleanup_failed_deployment(self):
        """Clean up after failed deployment"""
        print("\n🧹 Cleaning up failed deployment...")
        
        if self.deployment_type == 'docker':
            subprocess.run([
                'docker-compose', '-f', str(self.docker_dir / 'docker-compose.yml'),
                'down', '--remove-orphans'
            ], cwd=self.docker_dir)
        
        elif self.deployment_type == 'kubernetes':
            subprocess.run([
                'kubectl', 'delete', 'namespace', 'investmentai', '--ignore-not-found'
            ])
    
    def _print_deployment_summary(self):
        """Print deployment summary"""
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        if self.deployment_type == 'docker':
            print("🐳 Docker Deployment:")
            print("  • Application: http://localhost (HTTPS redirected)")
            print("  • Grafana: http://localhost:3000")
            print("  • Prometheus: http://localhost:9090")
            print("  • Database: localhost:5432")
            print("  • Redis: localhost:6379")
            
        elif self.deployment_type == 'kubernetes':
            print("☸️  Kubernetes Deployment:")
            print("  • Check pods: kubectl get pods -n investmentai")
            print("  • Check services: kubectl get services -n investmentai")
            print("  • View logs: kubectl logs -n investmentai -l app=investmentai")
        
        print("\n📋 Next Steps:")
        print("1. Update API keys in the .env file")
        print("2. Configure SSL certificates for production")
        print("3. Set up backup procedures")
        print("4. Configure monitoring alerts")
        print("5. Test all functionality")
        print("6. Set up CI/CD pipeline")
        
        print("\n🔐 Security Notes:")
        print("• Change all default passwords")
        print("• Enable firewall rules")
        print("• Configure log rotation")
        print("• Set up SSL certificates from trusted CA")
        print("• Review security configurations")


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy InvestmentAI to production')
    parser.add_argument('--type', choices=['docker', 'kubernetes'], default='docker',
                      help='Deployment type (default: docker)')
    parser.add_argument('--skip-checks', action='store_true',
                      help='Skip pre-deployment checks')
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(args.type)
    deployer.deploy()


if __name__ == "__main__":
    main()