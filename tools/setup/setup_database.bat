@echo off
echo Setting up Investment System Database...
echo.

REM Change to core directory
cd /d "%~dp0\..\..\core"

REM Run database setup
python database\setup.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Database setup failed!
    pause
    exit /b 1
)

echo.
echo ✅ Database setup completed successfully!
echo.
echo You can now use the database instead of JSON files.
echo Run your analysis scripts as normal - they will use the database.

pause