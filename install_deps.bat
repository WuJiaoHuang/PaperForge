@echo off
cd /d "%~dp0"
echo [PaperForge] Installing local dependencies into .\deps ...
if exist "D:\Anaconda\envs\pytorch_env\python.exe" (
  "D:\Anaconda\envs\pytorch_env\python.exe" -m pip install --target "%~dp0deps" -r requirements.txt
) else (
  python -m pip install --target "%~dp0deps" -r requirements.txt
)
if not exist "%~dp0deps\plantuml.jar" (
  echo [PaperForge] Downloading PlantUML renderer ...
  curl -L -o "%~dp0deps\plantuml.jar" https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/1.2024.8/plantuml-1.2024.8.jar
)
echo [PaperForge] Done. Run run.bat to start.
pause
