@echo off
REM ============================================================
REM  Market Overview Dashboard launcher
REM  Creates .venv + installs requirements on first run,
REM  then serves http://localhost:8050 (browser opens itself).
REM  Data auto-refreshes every 15 min (see config.py).
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo First run: creating virtual environment ...
    py -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" app.py

echo.
echo Dashboard stopped. Press any key to close this window.
pause >nul
