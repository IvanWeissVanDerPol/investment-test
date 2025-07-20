#!/usr/bin/env python3
"""
Pre-Analysis Hook for Investment Analysis System
Validates configuration and prerequisites before running analysis
"""

import json
import sys
import os
from pathlib import Path


def validate_config():
    """Validate configuration file exists and has required fields"""
    config_path = Path("tools/config.json")
    
    if not config_path.exists():
        return False, "Configuration file 'tools/config.json' not found"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = [
            'user_profile',
            'target_stocks', 
            'ai_robotics_etfs',
            'alert_thresholds'
        ]
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required config field: {field}"
        
        # Validate user profile
        user_profile = config.get('user_profile', {})
        if user_profile.get('dukascopy_balance', 0) <= 0:
            return False, "Invalid or missing dukascopy_balance in user profile"
        
        return True, "Configuration validated successfully"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in config file: {e}"
    except Exception as e:
        return False, f"Error validating config: {e}"


def check_dependencies():
    """Check if required Python packages are available"""
    required_packages = [
        'pandas',
        'numpy', 
        'yfinance',
        'requests',
        'beautifulsoup4'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"Missing required packages: {', '.join(missing_packages)}"
    
    return True, "All dependencies available"


def validate_api_access():
    """Check if API endpoints are accessible (basic connectivity)"""
    import requests
    
    # Test basic connectivity to financial APIs
    test_urls = [
        "https://query1.finance.yahoo.com/v1/finance/search?q=NVDA",
        "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    ]
    
    for url in test_urls:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code >= 400:
                return False, f"API endpoint not accessible: {url}"
        except requests.RequestException:
            return False, f"Network connectivity issue with: {url}"
    
    return True, "API endpoints accessible"


def check_output_directory():
    """Ensure reports directory exists and is writable"""
    reports_dir = Path("reports")
    
    if not reports_dir.exists():
        try:
            reports_dir.mkdir(exist_ok=True)
            return True, "Reports directory created"
        except Exception as e:
            return False, f"Cannot create reports directory: {e}"
    
    # Test write permissions
    test_file = reports_dir / "test_write.tmp"
    try:
        test_file.write_text("test")
        test_file.unlink()
        return True, "Reports directory is writable"
    except Exception as e:
        return False, f"Reports directory not writable: {e}"


def main():
    """Main pre-analysis validation"""
    print("🔍 Running pre-analysis validation...")
    
    checks = [
        ("Configuration", validate_config),
        ("Dependencies", check_dependencies), 
        ("API Access", validate_api_access),
        ("Output Directory", check_output_directory)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            success, message = check_func()
            status = "✅" if success else "❌"
            print(f"{status} {check_name}: {message}")
            
            if not success:
                all_passed = False
                
        except Exception as e:
            print(f"❌ {check_name}: Unexpected error - {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All pre-analysis checks passed. Ready to run investment analysis.")
        return 0
    else:
        print("\n❌ Pre-analysis validation failed. Please fix issues before running analysis.")
        return 1


if __name__ == "__main__":
    sys.exit(main())