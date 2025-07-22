@echo off
echo ===============================================
echo    YOUTUBE API INTEGRATION TEST SUITE
echo ===============================================
echo Testing YouTube Data API v3 integration...
echo.

cd /d "%~dp0\.."
python scripts\test_youtube_api.py

echo.
echo ===============================================
echo Test complete! Check output above for results.
echo.
echo If tests failed, see docs\guides\youtube_api_setup.md
echo for detailed setup instructions.
echo ===============================================
pause