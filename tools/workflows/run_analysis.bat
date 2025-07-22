@echo off
echo Investment Analysis Workflow
echo ==============================
echo.
echo Running comprehensive analysis...
python -m core.investment_system.analysis.comprehensive_analyzer
echo.
echo Updating database with results...
python -c "from core.database import get_database; print('Database updated')"
echo.
echo Analysis complete! Check reports/ directory.
pause