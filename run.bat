@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install_deps.bat first.
    pause
    exit /b 1
)

if not exist "tools\plantuml.jar" (
    echo [ERROR] PlantUML not found.
    echo Please run install_deps.bat first.
    pause
    exit /b 1
)

echo ========================================
echo PaperForge
echo ========================================
echo Starting backend at:
echo http://127.0.0.1:8000
echo.

start "" http://127.0.0.1:8000

uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

endlocal