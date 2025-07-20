@echo off
echo ===============================================
echo    INVESTMENT SYSTEM MONITORING
echo ===============================================
echo Starting continuous system monitoring...
echo.
echo Monitoring features:
echo - System health checks every 15 minutes
echo - Real-time price movement alerts
echo - API connectivity monitoring
echo - Cache performance tracking
echo - Daily health reports at 8:00 AM
echo.
echo Press Ctrl+C to stop monitoring
echo.

cd "C:\Users\jandr\Documents\ivan\tools"
python system_monitor.py --interval=15

echo.
echo ===============================================
echo Monitoring stopped.
echo ===============================================
pause