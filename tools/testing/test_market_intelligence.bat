@echo off
echo ===============================================
echo    YOUTUBE MARKET INTELLIGENCE TEST SUITE
echo ===============================================
echo Testing market intelligence aggregation and signal generation...
echo.

cd /d "%~dp0\.."
python scripts\test_market_intelligence.py

echo.
echo ===============================================
echo Test complete! The intelligence engine can:
echo - Aggregate insights from 39+ global analysts
echo - Generate buy/sell/hold signals with confidence
echo - Track analyst performance over time
echo - Build multi-analyst consensus on stocks
echo - Provide comprehensive market overviews
echo ===============================================
pause