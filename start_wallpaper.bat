@echo off
REM ============================================================
REM  Market Overview Dashboard - WALLPAPER mode
REM  No browser: paints the dashboard onto the Windows desktop
REM  background, refreshed every 15 min (see config.py).
REM  Keep this window open (minimized); closing it stops updates.
REM  Restore your old wallpaper any time via Windows Settings >
REM  Personalisation > Background (original path is saved in
REM  data\original_wallpaper.txt).
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo First run: creating virtual environment ...
    py -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" app.py --wallpaper

echo.
echo Wallpaper updates stopped. Press any key to close this window.
pause >nul
