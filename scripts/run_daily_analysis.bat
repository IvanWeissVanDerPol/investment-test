@echo off
echo ===============================================
echo    AUTOMATED INVESTMENT ANALYSIS SYSTEM
echo ===============================================
echo Starting daily analysis...
echo.

cd "C:\Users\jandr\Documents\ivan"
python -m src.investment_system.analysis.quick_analysis

echo.
echo ===============================================
echo Analysis complete! Check the reports folder.
echo ===============================================
pause