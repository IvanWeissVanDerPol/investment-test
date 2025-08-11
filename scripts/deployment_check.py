#!/usr/bin/env python
"""
Deployment Readiness Check Script
Run this before deploying to verify everything is ready
"""

import os
import sys
import subprocess
from pathlib import Path

def check_command(cmd, name):
    """Check if a command is available."""
    try:
        subprocess.run(cmd, capture_output=True, shell=True, check=True)
        return True, f"✅ {name} is available"
    except:
        return False, f"❌ {name} is not available"

def check_file(filepath, name):
    """Check if a file exists."""
    if Path(filepath).exists():
        return True, f"✅ {name} exists"
    else:
        return False, f"❌ {name} is missing"

def check_env_var(var, name):
    """Check if an environment variable is set."""
    value = os.getenv(var)
    if value and value != f"your_{var.lower()}_here":
        return True, f"✅ {name} is configured"
    else:
        return False, f"⚠️  {name} needs configuration"

def main():
    print("🚀 Investment System - Deployment Readiness Check\n")
    print("=" * 50)
    
    results = []
    critical_issues = []
    
    # Check critical files
    print("\n📁 Checking critical files...")
    files_to_check = [
        (".env", "Environment configuration"),
        ("requirements.txt", "Python dependencies"),
        ("deploy/docker/Dockerfile", "Docker configuration"),
        ("deploy/docker/docker-compose.yml", "Docker Compose"),
        ("alembic.ini", "Database migrations config"),
    ]
    
    for filepath, name in files_to_check:
        success, msg = check_file(filepath, name)
        results.append(msg)
        if not success and "Environment" in name:
            critical_issues.append("No .env file found")
    
    # Check commands
    print("\n🔧 Checking required commands...")
    commands_to_check = [
        ("python --version", "Python"),
        ("pip --version", "Pip"),
        ("docker --version", "Docker"),
        ("docker-compose --version", "Docker Compose"),
        ("git --version", "Git"),
    ]
    
    for cmd, name in commands_to_check:
        success, msg = check_command(cmd, name)
        results.append(msg)
    
    # Check Python packages
    print("\n📦 Checking Python packages...")
    try:
        import fastapi
        results.append("✅ FastAPI installed")
    except ImportError:
        results.append("❌ FastAPI not installed")
        critical_issues.append("FastAPI not installed")
    
    try:
        import sqlalchemy
        results.append("✅ SQLAlchemy installed")
    except ImportError:
        results.append("❌ SQLAlchemy not installed")
        critical_issues.append("SQLAlchemy not installed")
    
    try:
        import slowapi
        results.append("✅ SlowAPI installed")
    except ImportError:
        results.append("❌ SlowAPI not installed")
        critical_issues.append("SlowAPI not installed")
    
    # Check environment variables
    print("\n🔐 Checking environment configuration...")
    if Path(".env").exists():
        from dotenv import load_dotenv
        load_dotenv()
        
        env_vars = [
            ("DATABASE_URL", "Database URL"),
            ("SECRET_KEY", "Secret key"),
            ("JWT_SECRET_KEY", "JWT secret"),
        ]
        
        for var, name in env_vars:
            success, msg = check_env_var(var, name)
            results.append(msg)
            if not success:
                critical_issues.append(f"{name} not configured")
    
    # Test application startup
    print("\n🔥 Testing application startup...")
    try:
        # Try importing the main app
        sys.path.insert(0, "src")
        from investment_system.api import app
        results.append("✅ API module loads successfully")
    except Exception as e:
        results.append(f"❌ API module failed to load: {str(e)[:50]}")
        critical_issues.append("API module won't load")
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT READINESS REPORT")
    print("=" * 50 + "\n")
    
    for result in results:
        print(result)
    
    # Calculate score
    success_count = sum(1 for r in results if "✅" in r)
    total_count = len(results)
    score = (success_count / total_count) * 100
    
    print("\n" + "=" * 50)
    print(f"🎯 Readiness Score: {score:.0f}%")
    
    if critical_issues:
        print("\n⚠️  CRITICAL ISSUES TO FIX:")
        for issue in critical_issues:
            print(f"  - {issue}")
        print("\n❌ NOT READY FOR DEPLOYMENT")
        return 1
    elif score >= 80:
        print("\n✅ READY FOR DEPLOYMENT!")
        return 0
    else:
        print("\n⚠️  ALMOST READY - Review warnings above")
        return 0

if __name__ == "__main__":
    sys.exit(main())