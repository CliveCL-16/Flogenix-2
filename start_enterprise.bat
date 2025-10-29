@echo off
setlocal enabledelayedexpansion

:: Flogenix Enterprise System Startup Script (Windows)
:: This script starts the complete enterprise claims processing platform

echo.
echo ===============================================
echo 🚀 Starting Flogenix Enterprise Platform...
echo ===============================================
echo.

:: Check if we're in the right directory
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found. Please run from Flogenix-2 root directory.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo [ERROR] frontend\package.json not found. Please run from Flogenix-2 root directory.
    pause
    exit /b 1
)

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Prerequisites check passed
echo.

:: Setup and start backend
echo [INFO] Setting up backend environment...
cd backend

:: Create virtual environment if it doesn't exist
if not exist "vev" (
    echo [INFO] Creating Python virtual environment...
    python -m venv vev
)

:: Activate virtual environment
call vev\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements_enterprise.txt

:: Start backend server
echo [INFO] Starting enterprise backend server...
start "Flogenix Backend" cmd /k "python main_enterprise.py"

cd ..

:: Wait a moment for backend to start
timeout /t 5 /nobreak >nul

:: Setup and start frontend
echo [INFO] Setting up frontend environment...
cd frontend

:: Install dependencies
echo [INFO] Installing Node.js dependencies...
call npm install

:: Start frontend server
echo [INFO] Starting React development server...
start "Flogenix Frontend" cmd /k "npm run dev"

cd ..

:: Wait for services to start
echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

:: Display startup information
echo.
echo ===============================================
echo 🎉 Flogenix Enterprise Platform Started!
echo ===============================================
echo.
echo 🌐 Service URLs:
echo    • Frontend (React):     http://localhost:5173
echo    • Backend API:          http://localhost:8000
echo    • API Documentation:    http://localhost:8000/docs
echo    • Interactive API:      http://localhost:8000/redoc
echo.
echo 🔑 Default Admin Credentials:
echo    • Username: admin
echo    • Password: admin123
echo    • Role: SUPER_ADMIN
echo.
echo 📚 Quick Start Guide:
echo    1. Open http://localhost:5173 in your browser
echo    2. Login with admin credentials
echo    3. Navigate to Enterprise → Admin Portal
echo    4. Start processing claims with AI agents
echo.
echo 🤖 Enterprise Features:
echo    • Multi-Agent AI Processing
echo    • Real-time Fraud Detection
echo    • Advanced Analytics Dashboard
echo    • Role-based Access Control
echo    • Comprehensive Audit Trails
echo    • WebSocket Notifications
echo.
echo 📖 Documentation:
echo    • API Docs: http://localhost:8000/docs
echo    • README: .\README.md
echo    • Integration Guide: .\INTEGRATION_GUIDE.md
echo.
echo 🛑 To stop the platform:
echo    • Close this window and the service windows
echo    • Or run: scripts\stop_enterprise.bat
echo.
echo ===============================================
echo.

:: Open browser automatically
echo [INFO] Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo [INFO] Platform is running. Check the service windows for logs.
echo [INFO] Press any key to exit this script (services will continue running)...
pause >nul