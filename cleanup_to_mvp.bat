@echo off
REM MVP Cleanup Script for Windows - Remove 180+ non-revenue files
REM This script will delete ~14,000 lines of code to focus on MVP

echo ============================================================
echo            MVP CLEANUP SCRIPT - Windows Version
echo ============================================================
echo.
echo This will DELETE 180+ files (~14,000 lines of code)
echo Press Ctrl+C to cancel, or any key to continue...
pause > nul

REM Create backup branch with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set BACKUP_BRANCH=backup/pre-mvp-%datetime:~0,8%-%datetime:~8,6%

echo.
echo Creating backup branch: %BACKUP_BRANCH%
git checkout -b %BACKUP_BRANCH%
git add -A
git commit -m "backup: complete state before MVP cleanup"
git push origin %BACKUP_BRANCH% 2>nul || echo Warning: Could not push backup (may need auth)

REM Return to working branch
git checkout integration-claude-review

echo.
echo Starting deletion of non-MVP files...
echo.

REM Delete legacy core system (biggest chunk)
echo Removing legacy core system (60+ files, ~12,000 lines)...
rmdir /s /q src\core 2>nul

REM Delete old web application
echo Removing old Flask web app (15 files)...
rmdir /s /q src\web 2>nul

REM Delete Windows batch scripts
echo Removing batch script tools (40+ files)...
rmdir /s /q tools 2>nul

REM Delete MCP integrations
echo Removing MCP integrations...
rmdir /s /q mcp 2>nul

REM Delete scripts directory
echo Removing over-engineered scripts...
rmdir /s /q scripts 2>nul

REM Delete test files from root
echo Removing test files from root directory...
del /q test_*.py 2>nul

REM Delete planning documents
echo Removing planning documents...
rmdir /s /q planning 2>nul

REM Delete reference data
echo Removing reference JSON files...
rmdir /s /q reference 2>nul
rmdir /s /q data\reference 2>nul

REM Delete unnecessary documentation
echo Removing outdated documentation...
rmdir /s /q docs\01_project_overview 2>nul
rmdir /s /q docs\02_implementation 2>nul
rmdir /s /q docs\03_enhancements 2>nul
rmdir /s /q docs\05_investment_strategy 2>nul
rmdir /s /q docs\06_system_monitoring 2>nul
rmdir /s /q docs\07_research_and_analysis 2>nul

REM Delete kubernetes configs
echo Removing Kubernetes configs...
rmdir /s /q deploy\kubernetes 2>nul

REM Delete PowerBI configs
echo Removing PowerBI integration...
del /q src\config\powerbi_config.json 2>nul

REM Delete unused config JSONs
echo Removing redundant config files...
del /q src\config\analysis.json 2>nul
del /q src\config\content.json 2>nul
del /q src\config\data.json 2>nul
del /q src\config\system.json 2>nul

REM Clean cache directory
echo Cleaning cache directory...
rmdir /s /q cache 2>nul

REM Remove egg-info
echo Removing build artifacts...
for /d %%i in (src\*.egg-info) do rmdir /s /q "%%i" 2>nul

echo.
echo ============================================================
echo              CLEANUP COMPLETE!
echo ============================================================
echo.
echo Statistics:
echo   - Files deleted: ~180+
echo   - Lines removed: ~14,000
echo.
echo Ready for MVP development!
echo   - Next step: Run 'pip install -e .[dev]' to reinstall
echo   - Then: Run 'python -m investment_system' to start
echo.
echo Focus: Generate revenue with minimal, clean code
echo ============================================================