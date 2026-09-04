@echo off
echo ========================================================
echo   Starting Gait Abnormality Classification System
echo ========================================================
echo.

echo [1/3] Starting Flask Backend API (Port 5000)...
start "Gait Analysis Backend API" cmd /k "cd /d "%~dp0gait-abnormality-system" && py app/app.py"

echo [2/3] Starting React Frontend (Port 3000)...
start "GaitInsight Frontend" cmd /k "cd /d "%~dp0gait-insight-frontend" && npm.cmd run dev"

echo [3/3] Opening browser at http://localhost:3000...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo Both servers are launching!
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Demo Login:
echo   Email:    demo@gaitinsight.dev
echo   Password: demo1234
echo.
pause
