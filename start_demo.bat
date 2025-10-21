@echo off
echo.
echo ========================================
echo  FLOWGENIX - BUILDATHON DEMO STARTUP
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [1/5] Setting up backend environment...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

REM Check if .env exists
if not exist .env (
    echo.
    echo WARNING: .env file not found!
    echo Please create backend\.env with your OPENAI_API_KEY
    echo Example: OPENAI_API_KEY=sk-your-key-here
    echo.
    copy .env.example .env >nul 2>&1
    echo Created .env from template - please edit it with your API key
    pause
)

echo [2/5] Setting up frontend environment...
cd ..\frontend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

echo [3/5] Generating demo data...
cd ..
python demo_scenarios.py

echo [4/5] Starting backend server...
cd backend
call venv\Scripts\activate.bat
start "Flowgenix Backend" cmd /k "python main.py"
timeout /t 3 /nobreak >nul

echo [5/5] Starting frontend dashboard...
cd ..\frontend
call venv\Scripts\activate.bat
start "Flowgenix Frontend" cmd /k "streamlit run app.py"

echo.
echo ========================================
echo  FLOWGENIX IS STARTING UP!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend Dashboard: http://localhost:8501
echo API Docs: http://localhost:8000/docs
echo.
echo Both services are starting in separate windows...
echo Wait 10-15 seconds for full startup.
echo.
echo Press any key to open the demo guide...
pause >nul
start DEMO_GUIDE.md

echo.
echo Ready for your buildathon presentation! 🚀
echo.
pause