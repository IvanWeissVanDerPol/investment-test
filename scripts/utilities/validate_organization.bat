@echo off
echo Validating Project Organization...
echo.

cd /d "%~dp0\.."
python scripts\validate_project_organization.py

echo.
echo Validation complete. Press any key to exit...
pause >nul