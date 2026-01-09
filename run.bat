@echo off
echo ========================================
echo    AUTONOMOUS JOB APPLICATION AGENT
echo ========================================
echo.

REM Check if password is set
if "%LINKEDIN_PASSWORD%"=="" (
    echo WARNING: LINKEDIN_PASSWORD not set!
    set /p LINKEDIN_PASSWORD="Enter LinkedIn password: "
)

REM Change to script directory
cd /d "%~dp0"

REM Run the agent
python main.py %*

echo.
echo Agent stopped.
pause
