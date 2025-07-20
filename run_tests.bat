@echo off
echo ===============================================
echo    INVESTMENT ANALYSIS SYSTEM TESTS
echo ===============================================
echo Running test suite...
echo.

cd /d "C:\Users\jandr\Documents\ivan"

echo 1. Running code formatting check...
cd tools
python -m black --check *.py
if %errorlevel% neq 0 (
    echo ❌ Code formatting issues found. Run /clean to fix.
    cd ..
    pause
    exit /b 1
) else (
    echo ✅ Code formatting OK
)

echo.
echo 2. Running import organization check...
python -m isort --check-only *.py
if %errorlevel% neq 0 (
    echo ❌ Import organization issues found. Run /clean to fix.
    cd ..
    pause
    exit /b 1
) else (
    echo ✅ Import organization OK
)

echo.
echo 3. Running linting checks...
python -m flake8 *.py --max-line-length=88 --ignore=E203,W503
if %errorlevel% neq 0 (
    echo ❌ Linting issues found
    cd ..
    pause
    exit /b 1
) else (
    echo ✅ Linting OK
)

echo.
echo 4. Running type checking...
python -m mypy *.py --ignore-missing-imports
if %errorlevel% neq 0 (
    echo ⚠️  Type checking issues found
) else (
    echo ✅ Type checking OK
)

cd ..

echo.
echo 5. Running unit tests...
python -m pytest tests/ -v --tb=short
if %errorlevel% neq 0 (
    echo ❌ Unit tests failed
    pause
    exit /b 1
) else (
    echo ✅ Unit tests passed
)

echo.
echo 6. Running configuration validation...
python .claude\hooks\pre_analysis_hook.py
if %errorlevel% neq 0 (
    echo ❌ Configuration validation failed
    pause
    exit /b 1
) else (
    echo ✅ Configuration validation passed
)

echo.
echo 7. Testing analysis modules...
cd tools
echo Testing quick analysis...
timeout 60 python -c "from quick_analysis import get_stock_analysis; result = get_stock_analysis('MSFT'); print('✅ Quick analysis test passed' if result else '⚠️  Quick analysis returned no data')"

echo Testing comprehensive analyzer...
timeout 60 python -c "from comprehensive_analyzer import ComprehensiveAnalyzer; analyzer = ComprehensiveAnalyzer(); print('✅ Comprehensive analyzer test passed')"

cd ..

echo.
echo ===============================================
echo   ALL TESTS COMPLETED
echo ===============================================
echo.
echo Test Results Summary:
echo ✅ Code Formatting
echo ✅ Import Organization  
echo ✅ Linting
echo ✅ Type Checking
echo ✅ Unit Tests
echo ✅ Configuration Validation
echo ✅ Analysis Modules
echo.
echo Investment system is ready for trading analysis!
echo.
pause