@echo off
echo ===============================================
echo    YOUTUBE CHANNELS MONITORING SYSTEM
echo ===============================================
echo Monitoring stock analysis channels for new content...
echo.

cd /d "%~dp0\.."

echo Choose monitoring mode:
echo 1. Quick scan (last 24 hours, first 5 channels)
echo 2. Daily monitoring (last 24 hours, all channels) 
echo 3. Weekly review (last 7 days, all channels)
echo 4. Custom monitoring
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Running quick scan...
    python scripts\monitor_youtube_channels.py --days 1 --channels 5
) else if "%choice%"=="2" (
    echo Running daily monitoring...
    python scripts\monitor_youtube_channels.py --days 1
) else if "%choice%"=="3" (
    echo Running weekly review...
    python scripts\monitor_youtube_channels.py --days 7
) else if "%choice%"=="4" (
    echo.
    set /p days="Days to look back: "
    set /p channels="Max channels (blank for all): "
    set /p symbols="Target symbols (space-separated, blank for all): "
    
    if "%channels%"=="" (
        if "%symbols%"=="" (
            python scripts\monitor_youtube_channels.py --days %days%
        ) else (
            python scripts\monitor_youtube_channels.py --days %days% --symbols %symbols%
        )
    ) else (
        if "%symbols%"=="" (
            python scripts\monitor_youtube_channels.py --days %days% --channels %channels%
        ) else (
            python scripts\monitor_youtube_channels.py --days %days% --channels %channels% --symbols %symbols%
        )
    )
) else (
    echo Invalid choice. Running daily monitoring as default...
    python scripts\monitor_youtube_channels.py --days 1
)

echo.
echo ===============================================
echo Monitoring complete! Check the reports/ folder
echo for detailed JSON results.
echo ===============================================
pause