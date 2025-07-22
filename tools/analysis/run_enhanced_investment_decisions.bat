@echo off
echo ===============================================
echo    ENHANCED AI INVESTMENT DECISIONS
echo ===============================================
echo Running comprehensive investment analysis...
echo.
echo Combining:
echo - YouTube Intelligence (39+ global analysts)
echo - Claude AI Analysis ^& Market Insights
echo - Ethics Screening ^& Sustainability 
echo - Multi-dimensional Confidence Scoring
echo.

cd /d "%~dp0\.."

echo Select analysis mode:
echo 1. Quick Portfolio Analysis (default watchlist)
echo 2. Custom Stock Analysis (specify symbols)
echo 3. Full AI/Green Focus Analysis
echo 4. Risk Assessment Mode
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Running portfolio analysis on default watchlist...
    python scripts\run_enhanced_investment_decisions.py
) else if "%choice%"=="2" (
    echo.
    set /p symbols="Enter stock symbols (space-separated): "
    echo Running analysis for: %symbols%
    python scripts\run_enhanced_investment_decisions.py --symbols %symbols%
) else if "%choice%"=="3" (
    echo Running AI/Green focused analysis...
    python scripts\run_enhanced_investment_decisions.py --symbols NVDA MSFT GOOGL TSLA ICLN QCLN ARKQ BOTZ
) else if "%choice%"=="4" (
    echo Running risk assessment analysis...
    python scripts\run_enhanced_investment_decisions.py --symbols NVDA TSLA XOM AAPL
) else (
    echo Invalid choice. Running default portfolio analysis...
    python scripts\run_enhanced_investment_decisions.py
)

echo.
echo ===============================================
echo Analysis complete! Your investment decisions are ready.
echo.
echo Generated files in reports/ folder:
echo - enhanced_investment_decisions_[timestamp].json (complete analysis)
echo - investment_summary_[timestamp].txt (executive summary)
echo.
echo These decisions combine global intelligence with AI analysis!
echo ===============================================
pause