param(
  [string]$Password = "test1234"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"

Write-Host "=== GitHub Stars Release Watcher ===" -ForegroundColor Cyan
Write-Host ""

# Kill leftovers
Get-Process -Name "python*" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "uvicorn|app\.main" } |
  Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "node*" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "vite" } |
  Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start backend in its own window
Write-Host "[1/2] Starting backend (port 8000)..." -ForegroundColor Green
$beArgs = "/K", "cd /d `"$root`" && set APP_PASSWORD=$Password && $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList $beArgs

Start-Sleep -Seconds 3

# Start frontend in its own window
Write-Host "[2/2] Starting frontend (port 5173)..." -ForegroundColor Green
$feArgs = "/K", "cd /d `"$root\frontend`" && npm run dev"
Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList $feArgs

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Password: $Password" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close the server windows or press any key to stop both..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
