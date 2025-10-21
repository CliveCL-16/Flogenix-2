@echo off
echo 🏥 Flowgenix Frontend Setup
echo ========================

cd frontend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Frontend setup complete!
echo.
echo Next steps:
echo 1. Make sure backend is running
echo 2. Run: streamlit run app.py
echo.

pause