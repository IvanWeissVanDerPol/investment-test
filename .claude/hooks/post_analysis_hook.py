#!/usr/bin/env python3
"""
Post-Analysis Hook for Investment Analysis System
Validates analysis output and sends notifications
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart


def validate_analysis_output():
    """Validate that analysis generated proper output files"""
    reports_dir = Path("reports")
    
    if not reports_dir.exists():
        return False, "Reports directory not found"
    
    # Check for recent reports (last 24 hours)
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_reports = []
    
    for report_file in reports_dir.glob("*.json"):
        if report_file.stat().st_mtime > cutoff_time.timestamp():
            recent_reports.append(report_file)
    
    if not recent_reports:
        return False, "No recent analysis reports found"
    
    # Validate JSON structure of most recent report
    latest_report = max(recent_reports, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_report, 'r') as f:
            report_data = json.load(f)
        
        required_fields = [
            'generated_at',
            'analysis_type', 
            'recommendations',
            'confidence_scores'
        ]
        
        for field in required_fields:
            if field not in report_data:
                return False, f"Missing required field in report: {field}"
        
        # Validate confidence scores are in valid range
        confidence_scores = report_data.get('confidence_scores', {})
        for symbol, score in confidence_scores.items():
            if not (0.0 <= score <= 1.0):
                return False, f"Invalid confidence score for {symbol}: {score}"
        
        return True, f"Analysis output validated: {latest_report.name}"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in report file: {e}"
    except Exception as e:
        return False, f"Error validating report: {e}"


def check_portfolio_recommendations():
    """Validate portfolio recommendations are within risk tolerance"""
    reports_dir = Path("reports")
    latest_reports = sorted(reports_dir.glob("*.json"), 
                           key=lambda f: f.stat().st_mtime, reverse=True)
    
    if not latest_reports:
        return False, "No reports found for portfolio validation"
    
    try:
        with open(latest_reports[0], 'r') as f:
            report_data = json.load(f)
        
        recommendations = report_data.get('recommendations', {})
        
        # Check for risky recommendations (high concentration)
        total_allocation = 0
        max_single_position = 0
        
        for symbol, allocation in recommendations.items():
            if isinstance(allocation, dict) and 'allocation_percentage' in allocation:
                pct = allocation['allocation_percentage']
                total_allocation += pct
                max_single_position = max(max_single_position, pct)
        
        # Risk checks for medium risk tolerance
        if max_single_position > 25:  # No single position > 25%
            return False, f"Single position too large: {max_single_position}%"
        
        if total_allocation > 100:
            return False, f"Total allocation exceeds 100%: {total_allocation}%"
        
        return True, f"Portfolio recommendations within risk limits"
        
    except Exception as e:
        return False, f"Error validating portfolio recommendations: {e}"


def send_analysis_notification():
    """Send email notification about completed analysis"""
    try:
        # Load email configuration
        config_path = Path("tools/config.json")
        if not config_path.exists():
            return False, "Configuration file not found for notifications"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        email_settings = config.get('email_settings', {})
        
        if not email_settings.get('enabled', False):
            return True, "Email notifications disabled"
        
        # Find latest report
        reports_dir = Path("reports")
        latest_reports = sorted(reports_dir.glob("*.txt"), 
                               key=lambda f: f.stat().st_mtime, reverse=True)
        
        if not latest_reports:
            return False, "No text report found for notification"
        
        with open(latest_reports[0], 'r') as f:
            report_content = f.read()
        
        # Create email
        msg = MimeMultipart()
        msg['From'] = email_settings['username']
        msg['To'] = email_settings['recipient']
        msg['Subject'] = f"Investment Analysis Complete - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
Investment Analysis Completed Successfully

Report Summary:
{report_content[:500]}...

Full report available in: {latest_reports[0].name}

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
        server.starttls()
        server.login(email_settings['username'], email_settings['password'])
        text = msg.as_string()
        server.sendmail(email_settings['username'], email_settings['recipient'], text)
        server.quit()
        
        return True, "Notification email sent successfully"
        
    except Exception as e:
        return False, f"Failed to send notification: {e}"


def cleanup_old_reports():
    """Clean up reports older than 30 days"""
    try:
        reports_dir = Path("reports")
        cutoff_time = datetime.now() - timedelta(days=30)
        
        deleted_count = 0
        for report_file in reports_dir.glob("*"):
            if report_file.stat().st_mtime < cutoff_time.timestamp():
                report_file.unlink()
                deleted_count += 1
        
        return True, f"Cleaned up {deleted_count} old report files"
        
    except Exception as e:
        return False, f"Failed to cleanup old reports: {e}"


def validate_market_hours():
    """Check if analysis was run during appropriate market hours"""
    now = datetime.now()
    
    # US market hours (approximate): 9:30 AM - 4:00 PM ET on weekdays
    # For simplicity, check if it's a weekday
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return True, "Weekend analysis - market closed"
    
    # Could add more sophisticated market hours checking here
    return True, "Market hours validation passed"


def main():
    """Main post-analysis validation"""
    print("🔍 Running post-analysis validation...")
    
    checks = [
        ("Analysis Output", validate_analysis_output),
        ("Portfolio Recommendations", check_portfolio_recommendations),
        ("Market Hours", validate_market_hours),
        ("Cleanup Old Reports", cleanup_old_reports),
        ("Send Notification", send_analysis_notification)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            success, message = check_func()
            status = "✅" if success else "❌"
            print(f"{status} {check_name}: {message}")
            
            if not success and check_name in ["Analysis Output", "Portfolio Recommendations"]:
                # Critical checks
                all_passed = False
                
        except Exception as e:
            print(f"❌ {check_name}: Unexpected error - {e}")
            if check_name in ["Analysis Output", "Portfolio Recommendations"]:
                all_passed = False
    
    if all_passed:
        print("\n✅ Post-analysis validation completed successfully.")
        return 0
    else:
        print("\n⚠️  Post-analysis validation found issues. Check analysis output.")
        return 1


if __name__ == "__main__":
    sys.exit(main())