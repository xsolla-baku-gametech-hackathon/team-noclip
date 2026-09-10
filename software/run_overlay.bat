@echo off
cd /d "%~dp0"

if exist "xsolla_launcher.exe" (
    start "" "xsolla_launcher.exe" %*
    exit /b 0
)

start "" pythonw main.py %*
exit /b 0
