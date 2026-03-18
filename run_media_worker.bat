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

if "%DATABASE_URL%"=="" if not "%DESTINATION_DATABASE_URL%"=="" set "DATABASE_URL=%DESTINATION_DATABASE_URL%"
if "%DATABASE_URL%"=="" set "DATABASE_URL=mysql+pymysql://user:password@localhost/persistent_story_universe"

echo Starting media worker against %DATABASE_URL%

python -m backend.media_jobs.worker
