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
where npm.cmd >nul 2>nul
if %errorlevel%==0 (
  echo [PaperForge] Building Vue frontend ...
  pushd "%~dp0frontend"
  call npm.cmd install
  call npm.cmd run build
  popd
) else (
  echo [PaperForge] npm not found, frontend not built. Install Node.js then run "npm install && npm run build" in frontend directory.
)
echo [PaperForge] Done. Run run.bat to start.
pause
