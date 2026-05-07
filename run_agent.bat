@echo off
echo ============================================================
echo  Deployment Agent  —  Central Laptop
echo  Polls FastAPI server for pending deployments
echo ============================================================

REM Create venv if not present
if not exist "venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
)

REM Install dependencies
echo [SETUP] Installing dependencies...
venv\Scripts\pip install -q requests

REM Start the agent
echo [START] Agent running ...
venv\Scripts\python deployment_agent.py

pause
