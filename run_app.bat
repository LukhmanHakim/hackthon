@echo off
echo ============================================================
echo  Deployment Manager API
echo ============================================================

REM Create virtual environment if it does not exist
if not exist "venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
)

REM Install / upgrade dependencies
echo [SETUP] Installing dependencies...
venv\Scripts\pip install -q -r requirements.txt

REM Start FastAPI
echo [START] Launching API on http://0.0.0.0:8000
venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
