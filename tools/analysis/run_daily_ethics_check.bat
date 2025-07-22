@echo off
echo Starting Daily Portfolio Ethics Check...
echo.

cd /d "%~dp0\.."
python scripts\daily_ethics_check.py

echo.
echo Ethics check complete. Press any key to exit...
pause >nul