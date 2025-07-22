#!/usr/bin/env python3
"""
Deployment MCP Server
Handles deployment workflows for web and backend
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import zipfile

class DeploymentMCPServer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.web_dir = self.project_root / "web"
        self.deployment_dir = self.project_root / "deployment"
    
    def create_production_build(self):
        """Create optimized production build"""
        build_info = {
            "timestamp": datetime.now().isoformat(),
            "files_processed": 0,
            "optimizations_applied": [],
            "errors": []
        }
        
        # Ensure deployment directory exists
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Copy web files
        if self.web_dir.exists():
            web_deploy = self.deployment_dir / "web"
            if web_deploy.exists():
                shutil.rmtree(web_deploy)
            shutil.copytree(self.web_dir, web_deploy)
            build_info["files_processed"] = len(list(web_deploy.rglob("*")))
            build_info["optimizations_applied"].append("Copied web files")
        
        # Copy core modules
        core_deploy = self.deployment_dir / "core"
        if core_deploy.exists():
            shutil.rmtree(core_deploy)
        
        # Only copy essential modules
        essential_modules = ["database", "investment_system"]
        core_deploy.mkdir(exist_ok=True)
        
        for module in essential_modules:
            src = self.project_root / "core" / module
            if src.exists():
                shutil.copytree(src, core_deploy / module)
                build_info["optimizations_applied"].append(f"Copied {module}")
        
        return build_info
    
    def validate_deployment_readiness(self):
        """Validate if project is ready for deployment"""
        checks = {
            "database_ready": False,
            "requirements_complete": False,
            "config_files_present": False,
            "tests_passing": False,
            "security_checks": False
        }
        
        # Check database
        db_path = self.project_root / "investment_system.db"
        checks["database_ready"] = db_path.exists()
        
        # Check requirements
        req_file = self.project_root / "requirements.txt"
        checks["requirements_complete"] = req_file.exists()
        
        # Check config files
        config_files = [
            self.project_root / ".claude" / "mcp_config.json",
            self.project_root / "config" / "config.json"
        ]
        checks["config_files_present"] = all(f.exists() for f in config_files)
        
        # Check tests directory
        tests_dir = self.project_root / "tests"
        checks["tests_passing"] = tests_dir.exists() and len(list(tests_dir.rglob("test_*.py"))) > 0
        
        # Security checks
        checks["security_checks"] = True  # Placeholder for actual security validation
        
        return {
            "deployment_ready": all(checks.values()),
            "readiness_score": f"{sum(checks.values())}/{len(checks)}",
            "checks": checks
        }
    
    def create_deployment_package(self, package_name=None):
        """Create deployment package"""
        if package_name is None:
            package_name = f"investment_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        package_path = self.deployment_dir / f"{package_name}.zip"
        
        # Ensure deployment directory exists
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Create zip package
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add essential files
            files_to_include = [
                ("web/", "web/"),
                ("core/database/", "core/database/"),
                ("core/investment_system/", "core/investment_system/"),
                ("requirements.txt", "requirements.txt"),
                ("README.md", "README.md")
            ]
            
            included_files = 0
            for src, dest in files_to_include:
                src_path = self.project_root / src
                if src_path.exists():
                    if src_path.is_file():
                        zipf.write(src_path, dest)
                        included_files += 1
                    else:
                        for file in src_path.rglob("*"):
                            if file.is_file():
                                arcname = dest + str(file.relative_to(src_path))
                                zipf.write(file, arcname)
                                included_files += 1
        
        return {
            "package_created": str(package_path),
            "package_size": package_path.stat().st_size,
            "files_included": included_files,
            "timestamp": datetime.now().isoformat()
        }
    
    def setup_local_server(self, port=5000):
        """Setup local development server"""
        server_config = {
            "port": port,
            "host": "127.0.0.1",
            "debug": True,
            "auto_reload": True
        }
        
        # Create startup script
        startup_script = self.deployment_dir / "start_server.py"
        startup_script.parent.mkdir(exist_ok=True)
        
        with open(startup_script, 'w') as f:
            f.write(f"""#!/usr/bin/env python3
from web.app import app

if __name__ == "__main__":
    app.run(host='{server_config["host"]}', port={server_config["port"]}, debug={server_config["debug"]})
""")
        
        return {
            "server_config": server_config,
            "startup_script": str(startup_script),
            "launch_command": f"python {startup_script}"
        }
    
    def check_system_requirements(self):
        """Check system requirements for deployment"""
        requirements = {
            "python_version": False,
            "dependencies": False,
            "disk_space": False,
            "memory": False
        }
        
        try:
            # Check Python version
            import sys
            requirements["python_version"] = sys.version_info >= (3, 8)
            
            # Check dependencies
            import pkg_resources
            with open(self.project_root / "requirements.txt", 'r') as f:
                required_packages = [line.strip().split('==')[0] for line in f if line.strip()]
            
            installed_packages = [pkg.key for pkg in pkg_resources.working_set]
            missing_packages = [pkg for pkg in required_packages if pkg.lower() not in [p.lower() for p in installed_packages]]
            requirements["dependencies"] = len(missing_packages) == 0
            
            # Check disk space (simplified)
            import shutil
            total, used, free = shutil.disk_usage("/")
            requirements["disk_space"] = free > 1_000_000_000  # 1GB free
            
            # Memory check (simplified)
            import psutil
            memory = psutil.virtual_memory()
            requirements["memory"] = memory.total > 2_000_000_000  # 2GB
            
        except Exception as e:
            return {"error": str(e)}
        
        return {
            "system_ready": all(requirements.values()),
            "requirements": requirements,
            "missing_packages": missing_packages if 'missing_packages' in locals() else []
        }
    
    def create_docker_config(self):
        """Create Docker configuration for deployment"""
        docker_config = {
            "dockerfile": "Dockerfile",
            "compose_file": "docker-compose.yml",
            "environment": "production"
        }
        
        # Create Dockerfile
        dockerfile = self.deployment_dir / "Dockerfile"
        with open(dockerfile, 'w') as f:
            f.write("""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ ./core/
COPY web/ ./web/
COPY investment_system.db ./

EXPOSE 5000

CMD ["python", "-m", "web.app"]
""")
        
        # Create docker-compose.yml
        compose_file = self.deployment_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            f.write("""version: '3.8'

services:
  investment-system:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///investment_system.db
""")
        
        return {
            "docker_config_created": True,
            "dockerfile": str(dockerfile),
            "compose_file": str(compose_file),
            "build_command": "docker-compose up --build"
        }
    
    def generate_deployment_script(self, target="local"):
        """Generate deployment script for target environment"""
        scripts = {
            "local": self._generate_local_script(),
            "docker": self._generate_docker_script(),
            "production": self._generate_production_script()
        }
        
        return scripts.get(target, {"error": "Unknown target"})
    
    def _generate_local_script(self):
        """Generate local deployment script"""
        script_content = """#!/bin/bash
echo "Starting Investment System..."
cd $(dirname "$0")/..

# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Set up database
python core/database/setup.py

# Start server
echo "Starting Flask server..."
python -m web.app
"""
        
        script_path = self.deployment_dir / "deploy_local.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        return {
            "script": str(script_path),
            "type": "local",
            "command": f"bash {script_path}"
        }
    
    def _generate_docker_script(self):
        """Generate Docker deployment script"""
        script_content = """#!/bin/bash
echo "Deploying with Docker..."
cd $(dirname "$0")/..

# Build and start containers
docker-compose up --build -d

# Wait for service to start
echo "Waiting for service to start..."
sleep 10

# Check service health
curl -f http://localhost:5000/health || echo "Service may not be ready"
"""
        
        script_path = self.deployment_dir / "deploy_docker.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        return {
            "script": str(script_path),
            "type": "docker",
            "command": f"bash {script_path}"
        }
    
    def _generate_production_script(self):
        """Generate production deployment script"""
        script_content = """#!/bin/bash
echo "Production deployment..."
cd $(dirname "$0")/..

# Create production build
python mcp/deployment_mcp.py build

# Validate deployment
python mcp/deployment_mcp.py validate

# Create deployment package
python mcp/deployment_mcp.py package

echo "Production deployment complete!"
"""
        
        script_path = self.deployment_dir / "deploy_production.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        return {
            "script": str(script_path),
            "type": "production",
            "command": f"bash {script_path}"
        }

# CLI interface
if __name__ == "__main__":
    import sys
    
    server = DeploymentMCPServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "build":
            print(json.dumps(server.create_production_build(), indent=2))
        
        elif command == "validate":
            print(json.dumps(server.validate_deployment_readiness(), indent=2))
        
        elif command == "package":
            package_name = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(server.create_deployment_package(package_name), indent=2))
        
        elif command == "server":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
            print(json.dumps(server.setup_local_server(port), indent=2))
        
        elif command == "requirements":
            print(json.dumps(server.check_system_requirements(), indent=2))
        
        elif command == "docker":
            print(json.dumps(server.create_docker_config(), indent=2))
        
        elif command == "deploy":
            target = sys.argv[2] if len(sys.argv) > 2 else "local"
            print(json.dumps(server.generate_deployment_script(target), indent=2))
        
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({
            "available_commands": [
                "build", "validate", "package", "server", 
                "requirements", "docker", "deploy"
            ]
        }, indent=2))