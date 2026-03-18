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

if "%SOURCE_DATABASE_URL%"=="" set "SOURCE_DATABASE_URL=mysql+pymysql://rtcwa:!Wdfez69@localhost/stories"
if "%DESTINATION_DATABASE_URL%"=="" if not "%DATABASE_URL%"=="" set "DESTINATION_DATABASE_URL=%DATABASE_URL%"
if "%DESTINATION_DATABASE_URL%"=="" set "DESTINATION_DATABASE_URL=mysql+pymysql://rtcwa:!Wdfez69@localhost/persistent_story_universe"

echo Source database: %SOURCE_DATABASE_URL%
echo Destination database: %DESTINATION_DATABASE_URL%
echo Running classical story import...

python -m backend.scripts.import_classical_stories

if errorlevel 1 (
    echo Classical story import failed.
    exit /b 1
)

echo Classical story import completed successfully.
