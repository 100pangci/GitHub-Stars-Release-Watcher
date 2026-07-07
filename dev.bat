@echo off
cd /d "%~dp0"

echo === GitHub Stars Release Watcher ===
echo.

:: Kill leftovers
taskkill /f /im python.exe 2>nul >nul
taskkill /f /im node.exe 2>nul >nul
timeout /t 2 /nobreak >nul

:: Start backend
echo [1/2] Starting backend (port 8000)...
start "Backend" cmd /k "set APP_PASSWORD=test1234 && C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 4 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend (port 5173)...
start "Frontend" cmd /k "cd /d frontend && npm run dev"

echo.
echo =====================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Password: test1234
echo =====================================
echo.
echo Close the server windows to stop.
pause
