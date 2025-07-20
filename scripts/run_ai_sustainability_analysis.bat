@echo off
echo Starting AI-Powered Sustainability Analysis...
echo.

cd /d "%~dp0\.."
python scripts\run_ai_sustainability_analysis.py

echo.
echo AI analysis complete. Press any key to exit...
pause >nul