@echo off
title Xsolla Game Recap Launcher
cd /d "%~dp0"

echo ========================================================
echo   XSOLLA GAME RECAP OVERLAY & GAMEBAR
echo ========================================================
echo Starting background game watcher and in-game GameBar...
echo Shortcut to open overlay during game: [Ctrl + Shift + X] (or Alt + X)
echo.

python main.py %*
pause
