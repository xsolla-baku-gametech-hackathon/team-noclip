@echo off
echo ===================================================
echo   Xsolla Game Recap - FastAPI Middleware Launcher
echo ===================================================
cd /d "%~dp0"
echo Starting backend on http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
