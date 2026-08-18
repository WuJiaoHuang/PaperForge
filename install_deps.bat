@echo off
cd /d "%~dp0"
echo [PaperForge] Installing local dependencies into .\deps ...
if exist "D:\Anaconda\envs\pytorch_env\python.exe" (
  "D:\Anaconda\envs\pytorch_env\python.exe" -m pip install --target "%~dp0deps" -r requirements.txt
) else (
  python -m pip install --target "%~dp0deps" -r requirements.txt
)
echo [PaperForge] Done. Run run.bat to start.
pause
