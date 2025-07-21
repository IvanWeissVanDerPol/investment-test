@echo off
echo ===============================================
echo    YOUTUBE CONTENT PROCESSOR TEST SUITE
echo ===============================================
echo Testing stock analysis and sentiment extraction...
echo.

cd /d "%~dp0\.."
python scripts\test_youtube_content_processor.py

echo.
echo ===============================================
echo Test complete! Check output above for results.
echo.
echo The content processor can extract:
echo - Stock mentions with sentiment analysis
echo - Buy/sell/hold recommendations  
echo - Price targets and time horizons
echo - Market trends and insights
echo - Multi-analyst consensus analysis
echo ===============================================
pause