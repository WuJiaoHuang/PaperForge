@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo PaperForge - Install Dependencies
echo ========================================

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not found.
    echo Please install uv first.
    pause
    exit /b 1
)

echo.
echo [1/3] Syncing Python environment...
uv sync

if errorlevel 1 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Checking PlantUML...

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
echo [3/3] Checking Python environment...

uv run python -c "import fastapi, uvicorn, docx, openai, dotenv, matplotlib; print('Python environment OK')"

if errorlevel 1 (
    echo [ERROR] Python environment check failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully.
echo ========================================
echo.
pause

endlocal
