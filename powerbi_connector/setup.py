#!/usr/bin/env python3
"""
Setup script for Power BI Connector
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_environment():
    """Setup environment file"""
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        subprocess.check_call(['copy', '.env.example', '.env'], shell=True)
        print("⚠️  Please edit .env file with your Power BI credentials")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function"""
    print("🚀 Setting up Power BI Connector...")
    
    try:
        install_requirements()
        setup_environment()
        
        print("\n✅ Setup complete!")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your Power BI credentials")
        print("2. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())