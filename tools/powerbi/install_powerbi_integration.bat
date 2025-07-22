@echo off
REM Power BI Integration Installation Script
REM Installs and configures all Power BI components for the investment system

echo ========================================
echo Power BI Integration Setup
echo ========================================
echo.

REM Change to project root
cd /d "%~dp0\..\.."

echo 📦 Installing required Python packages...
pip install msal requests pandas

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install Python packages
    pause
    exit /b 1
)

echo ✅ Python packages installed
echo.

echo 🔧 Creating Power BI configuration...
python tools\powerbi\setup_powerbi_desktop.py setup

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create Power BI configuration
    pause
    exit /b 1
)

echo ✅ Power BI configuration created
echo.

echo 📊 Exporting sample data...
python -m mcp.powerbi_mcp export

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to export sample data
    pause
    exit /b 1
)

echo ✅ Sample data exported
echo.

echo 🎉 Power BI Integration Setup Complete!
echo.
echo 📖 Next Steps:
echo 1. Configure Azure AD authentication:
echo    - Run: python tools\powerbi\setup_powerbi_auth.py setup
echo.
echo 2. Open Power BI Desktop and follow the setup guide:
echo    - Guide: powerbi_project\templates\powerbi_desktop_setup_guide.md
echo.
echo 3. Use automation tools:
echo    - Daily export: tools\powerbi\run_powerbi_workflow.bat
echo    - Validation: python tools\powerbi\validate_powerbi_data.py
echo.

pause