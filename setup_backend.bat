@echo off
echo 🏥 Flowgenix Backend Setup
echo ========================

cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Backend setup complete!
echo.
echo Next steps:
echo 1. Copy .env.example to .env and add your OpenAI API key
echo 2. Run: python main.py
echo.

pause