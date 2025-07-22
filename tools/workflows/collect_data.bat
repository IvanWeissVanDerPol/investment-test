@echo off
echo Data Collection Workflow
echo ==========================
echo.
echo Collecting market data...
python -m core.investment_system.data.market_data_collector
echo.
echo Collecting news sentiment...
python -m core.investment_system.analysis.news_sentiment_analyzer
echo.
echo Data collection complete! Check cache/ directory.
pause