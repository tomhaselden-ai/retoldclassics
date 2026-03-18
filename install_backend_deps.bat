@echo off
if exist .\venv\Scripts\activate.bat (
    call .\venv\Scripts\activate.bat
) else (
    call .\.venv\Scripts\activate.bat
)
pip install fastapi uvicorn sqlalchemy pymysql passlib[bcrypt] python-jose[cryptography] email-validator
