@echo off
setlocal

cd /d "%~dp0\frontend_pwa"

if exist "..\local_backend_env.bat" (
    call "..\local_backend_env.bat"
)

if not exist "package.json" (
    echo frontend_pwa\package.json was not found.
    exit /b 1
)

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
    if errorlevel 1 exit /b 1
)

if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5173"
if /I "%~1"=="remote" (
    set "FRONTEND_HOST=0.0.0.0"
) else if "%FRONTEND_HOST%"=="" (
    set "FRONTEND_HOST=127.0.0.1"
)

echo Starting frontend at http://%FRONTEND_HOST%:%FRONTEND_PORT%
if /I "%FRONTEND_HOST%"=="0.0.0.0" (
    echo Frontend will be reachable from other devices at http://YOUR-PC-IP:%FRONTEND_PORT%
)

call npm run dev -- --host %FRONTEND_HOST% --port %FRONTEND_PORT%
