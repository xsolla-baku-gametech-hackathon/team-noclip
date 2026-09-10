@echo off
echo ===================================================
echo   Xsolla Game Recap - Quick Rebuild ^& Launcher
echo ===================================================
echo Stopping any running Stardew/SMAPI instances...
taskkill /F /IM StardewModdingAPI.exe /T 2>nul
taskkill /F /IM "Stardew Valley.exe" /T 2>nul

echo Recompiling XsollaGameRecap mod...
cd /d "%~dp0"
dotnet build XsollaGameRecap\XsollaGameRecap.csproj -c Debug
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed! Check compiler output.
    pause
    exit /b %ERRORLEVEL%
)

echo [SUCCESS] Mod deployed! Launching Stardew Valley...
cd /d "C:\Program Files (x86)\Steam\steamapps\common\Stardew Valley"
start "" StardewModdingAPI.exe
echo Game is starting in interactive window.
