@echo off
echo ===============================================
echo   INVESTMENT ANALYSIS SYSTEM SETUP
echo ===============================================
echo Setting up development environment...
echo.

cd /d "C:\Users\jandr\Documents\ivan"

echo 1. Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing production dependencies
    pause
    exit /b 1
)

echo.
echo 2. Installing development dependencies...
pip install pytest pytest-cov black isort flake8 mypy pre-commit psutil memory-profiler
if %errorlevel% neq 0 (
    echo Error installing development dependencies
    pause
    exit /b 1
)

echo.
echo 3. Setting up pre-commit hooks...
pre-commit install
if %errorlevel% neq 0 (
    echo Warning: Pre-commit setup failed
)

echo.
echo 4. Creating necessary directories...
if not exist "tests" mkdir tests
if not exist "reports" mkdir reports
if not exist "cache" mkdir cache
if not exist ".claude\commands" mkdir .claude\commands
if not exist ".claude\hooks" mkdir .claude\hooks

echo.
echo 5. Validating configuration...
cd tools
python -c "import json; config = json.load(open('config.json')); print('✅ Configuration valid')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Configuration validation failed
    pause
    exit /b 1
)

echo.
echo 6. Testing analysis modules...
python -c "from quick_analysis import get_stock_analysis; print('✅ Quick analysis module ready')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Quick analysis module test failed
)

python -c "from comprehensive_analyzer import ComprehensiveAnalyzer; print('✅ Comprehensive analyzer ready')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Comprehensive analyzer test failed
)

cd ..

echo.
echo 7. Running pre-analysis validation...
python .claude\hooks\pre_analysis_hook.py
if %errorlevel% neq 0 (
    echo ❌ Pre-analysis validation failed
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   SETUP COMPLETE!
echo ===============================================
echo.
echo Available commands:
echo   run_daily_analysis.bat     - Quick daily analysis
echo   run_comprehensive_analysis.bat - Full analysis  
echo   run_system_monitor.bat     - Start system monitoring
echo   run_tests.bat             - Run test suite
echo.
echo Slash commands available in Claude Code:
echo   /clean     - Format and lint code
echo   /analyze   - Comprehensive code analysis
echo   /optimize  - Performance optimization analysis
echo   /test      - Run test suite
echo   /portfolio - Portfolio management commands
echo   /monitor   - System monitoring commands
echo.
echo Development workflow:
echo   1. Use /clean before committing code changes
echo   2. Run /test to ensure quality
echo   3. Use /portfolio for investment analysis
echo   4. Monitor system health with /monitor
echo.
echo Investment focus: AI/Robotics stocks and ETFs
echo Portfolio: $900 (Dukascopy), Medium risk tolerance
echo.
pause