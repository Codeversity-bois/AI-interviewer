@echo off
REM Quick start script for testing frontend with microservice

echo ========================================
echo Starting Microservice and Frontend
echo ========================================
echo.

REM Check if microservice is already running
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Microservice already running on port 8001
) else (
    echo [INFO] Starting microservice...
    start "Microservice" cmd /k "cd /d %~dp0 && uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload"
    timeout /t 3 /nobreak >nul
)

REM Start frontend server
echo [INFO] Starting frontend server on port 8080...
cd frontend_client
start "Frontend Server" cmd /k "python -m http.server 8080"
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Microservice: http://localhost:8001
echo Frontend:     http://localhost:8080/live_interview.html
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:8080/live_interview.html
