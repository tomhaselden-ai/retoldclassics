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

python -m backend.scripts.character_canon_batch %*
pause