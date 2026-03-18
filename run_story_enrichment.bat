@echo off
setlocal

cd /d "%~dp0"

if exist ".\local_backend_env.bat" (
    call ".\local_backend_env.bat"
)

if exist ".\venv\Scripts\activate.bat" (
    call ".\venv\Scripts\activate.bat"
) else if exist ".\.venv\Scripts\activate.bat" (
    call ".\.venv\Scripts\activate.bat"
) else (
    echo No virtual environment was found. Create one in .\venv or .\.venv first.
    exit /b 1
)

if "%OPENAI_API_KEY%"=="" (
    echo OPENAI_API_KEY is not set.
    echo Add it to local_backend_env.bat or set it in this shell before running.
    exit /b 1
)

if "%OPENAI_MODEL%"=="" set "OPENAI_MODEL=gpt-4o-mini"
if "%OPENAI_TIMEOUT_SECONDS%"=="" set "OPENAI_TIMEOUT_SECONDS=240"
if "%OPENAI_MAX_RETRIES%"=="" set "OPENAI_MAX_RETRIES=2"

python -c "import mysql.connector" >nul 2>&1
if errorlevel 1 (
    echo Installing mysql-connector-python into the active virtual environment...
    python -m pip install mysql-connector-python
    if errorlevel 1 exit /b 1
)

echo Running story enrichment with model %OPENAI_MODEL%...
python injest\story_enrichment_pipeline.py
