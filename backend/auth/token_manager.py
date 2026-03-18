import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.auth.auth_service import get_account_by_email, get_account_by_id
from backend.config.settings import JWT_SECRET
from backend.db.database import get_db


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(account_id: int, email: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(account_id),
        "account_id": account_id,
        "email": email,
        "token_type": "access",
        "exp": expire_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def create_reset_token(account_id: int, email: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(account_id),
        "account_id": account_id,
        "email": email,
        "token_type": "reset",
        "exp": expire_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    payload = decode_token(credentials.credentials)

    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    account_id = payload.get("account_id")
    email = payload.get("email")
    if account_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload",
        )

    account = get_account_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
        )

    if account.email != email:
        refreshed = get_account_by_email(db, email)
        if refreshed is None or refreshed.account_id != account.account_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token payload",
            )

    return account
