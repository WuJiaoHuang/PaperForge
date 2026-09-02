@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo PaperForge - Install Dependencies
echo ========================================

echo.
echo [1/4] Installing Python dependencies...
if exist "D:\Anaconda\envs\pytorch_env\python.exe" (
    "D:\Anaconda\envs\pytorch_env\python.exe" -m pip install -r requirements.txt
) else (
    python -m pip install -r requirements.txt
)

if errorlevel 1 (
    echo [ERROR] Python dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [2/4] Checking PlantUML...

if not exist "tools" mkdir "tools"

if not exist "tools\plantuml.jar" (
    echo Downloading PlantUML...
    curl.exe -L -o "tools\plantuml.jar" "https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/1.2024.8/plantuml-1.2024.8.jar"

    if errorlevel 1 (
        echo [ERROR] PlantUML download failed.
        pause
        exit /b 1
    )
)

echo.
echo [3/4] Checking Python environment...

if exist "D:\Anaconda\envs\pytorch_env\python.exe" (
    "D:\Anaconda\envs\pytorch_env\python.exe" -c "import fastapi, uvicorn, docx, openai, dotenv, matplotlib; print('Python environment OK')"
) else (
    python -c "import fastapi, uvicorn, docx, openai, dotenv, matplotlib; print('Python environment OK')"
)

if errorlevel 1 (
    echo [ERROR] Python environment check failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Building Vue frontend...
where npm.cmd >nul 2>nul
if %errorlevel%==0 (
    pushd "%~dp0frontend"
    call npm.cmd install
    call npm.cmd run build
    popd
) else (
    echo [WARN] npm not found, frontend not built. Install Node.js then run "npm install && npm run build" in frontend directory.
)

echo.
echo ========================================
echo Installation completed successfully.
echo ========================================
echo.
pause

endlocal
