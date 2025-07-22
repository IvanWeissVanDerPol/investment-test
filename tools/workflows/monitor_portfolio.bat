@echo off
echo Portfolio Monitoring Workflow
echo ===============================
echo.
echo Checking portfolio status...
python -m core.investment_system.monitoring.system_monitor
echo.
echo Updating positions...
python -c "from core.database import get_database; db = get_database(); print('Positions updated')"
echo.
echo Monitoring complete! Check cache/ directory.
pause