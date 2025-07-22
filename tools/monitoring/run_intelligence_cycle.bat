@echo off
echo ===============================================
echo    YOUTUBE MARKET INTELLIGENCE CYCLE
echo ===============================================
echo Running complete market intelligence analysis...
echo.

cd /d "%~dp0\.."

echo Select intelligence cycle type:
echo 1. Quick Intelligence (last 24 hours)
echo 2. Daily Intelligence (comprehensive 24h analysis) 
echo 3. Weekly Intelligence (7 days of data)
echo 4. Custom timeframe
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Running quick intelligence cycle...
    python scripts\run_intelligence_cycle.py --days 1 --quiet
) else if "%choice%"=="2" (
    echo Running daily intelligence cycle...
    python scripts\run_intelligence_cycle.py --days 1
) else if "%choice%"=="3" (
    echo Running weekly intelligence cycle...
    python scripts\run_intelligence_cycle.py --days 7
) else if "%choice%"=="4" (
    echo.
    set /p days="Days to analyze: "
    set /p output="Output directory (blank for 'reports'): "
    
    if "%output%"=="" (
        python scripts\run_intelligence_cycle.py --days %days%
    ) else (
        python scripts\run_intelligence_cycle.py --days %days% --output %output%
    )
) else (
    echo Invalid choice. Running daily intelligence as default...
    python scripts\run_intelligence_cycle.py --days 1
)

echo.
echo ===============================================
echo Intelligence cycle complete! 
echo.
echo Generated files in reports/ folder:
echo - market_intelligence_[timestamp].json (complete data)
echo - intelligence_summary_[timestamp].txt (executive summary)  
echo - investment_signals_[timestamp].csv (signals for spreadsheet)
echo.
echo These signals are ready for your AI investment decisions!
echo ===============================================
pause