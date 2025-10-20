stea@echo off
echo Starting Macallan RF Performance Tool...
echo.

REM Change to the correct directory
cd /d "C:\Users\Mike Martin\macallan_rf_perf_tool"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
python src\main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)



