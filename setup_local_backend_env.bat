@echo off
setlocal

if exist local_backend_env.bat (
    echo local_backend_env.bat already exists. No changes made.
    exit /b 0
)

if not exist local_backend_env.example.bat (
    echo local_backend_env.example.bat was not found.
    exit /b 1
)

copy /Y local_backend_env.example.bat local_backend_env.bat >nul
echo Created local_backend_env.bat from local_backend_env.example.bat
echo Fill in your real local secrets before starting the backend.

