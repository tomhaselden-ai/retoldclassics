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
if "%JWT_SECRET%"=="" set "JWT_SECRET=your_jwt_secret"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if /I "%~1"=="remote" (
    set "BACKEND_HOST=0.0.0.0"
) else if "%BACKEND_HOST%"=="" (
    set "BACKEND_HOST=127.0.0.1"
)

echo Starting backend at http://%BACKEND_HOST%:%BACKEND_PORT%
echo Using database: %DATABASE_URL%
if /I "%BACKEND_HOST%"=="0.0.0.0" (
    echo Backend will be reachable from other devices at http://YOUR-PC-IP:%BACKEND_PORT%
)

uvicorn backend.main:app --host %BACKEND_HOST% --port %BACKEND_PORT% --reload
