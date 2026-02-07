# Quick start script for testing frontend with microservice

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Microservice and Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if microservice is already running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[INFO] Microservice already running on port 8001" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Starting microservice..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; uvicorn live_interview_service.service:app --host 0.0.0.0 --port 8001 --reload"
    Start-Sleep -Seconds 3
}

# Start frontend server
Write-Host "[INFO] Starting frontend server on port 8080..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "frontend_client"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; python -m http.server 8080"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Microservice: http://localhost:8001" -ForegroundColor White
Write-Host "Frontend:     http://localhost:8080/live_interview.html" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow

Start-Process "http://localhost:8080/live_interview.html"
