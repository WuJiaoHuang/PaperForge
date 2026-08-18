@echo off
setlocal
cd /d "%~dp0"

if not exist "deps" (
  echo [PaperForge] Local dependencies not found.
  echo Run install_deps.bat first, then run this script again.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\deps"

if exist "D:\Anaconda\envs\pytorch_env\python.exe" (
  set "PYEXE=D:\Anaconda\envs\pytorch_env\python.exe"
) else (
  set "PYEXE=python"
)

echo [PaperForge] Starting demo at http://127.0.0.1:8000
start "" http://127.0.0.1:8000
"%PYEXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
endlocal
