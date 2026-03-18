from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from backend.accounts.account_service import get_account_profile, update_account_profile
from backend.api.rate_limit import build_rate_limit_dependency
from backend.auth.auth_service import authenticate_account, register_account
from backend.auth.password_reset import create_password_reset_token, reset_password_with_token
from backend.auth.token_manager import create_access_token, get_current_account
from backend.config.settings import (
    RATE_LIMIT_LOGIN_REQUESTS,
    RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    RATE_LIMIT_RESET_REQUESTS,
    RATE_LIMIT_RESET_WINDOW_SECONDS,
)
from backend.db.database import get_db


router = APIRouter()
login_rate_limit = build_rate_limit_dependency(
    "auth_login",
    RATE_LIMIT_LOGIN_REQUESTS,
    RATE_LIMIT_LOGIN_WINDOW_SECONDS,
)
reset_rate_limit = build_rate_limit_dependency(
    "auth_reset",
    RATE_LIMIT_RESET_REQUESTS,
    RATE_LIMIT_RESET_WINDOW_SECONDS,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirmRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=255)


class AccountProfileResponse(BaseModel):
    account_id: int
    email: EmailStr
    subscription_level: str | None
    story_security: str | None
    allowed_classics_authors: list[str] | None
    created_at: object

    model_config = ConfigDict(from_attributes=True)


class AccountUpdateRequest(BaseModel):
    subscription_level: str = Field(min_length=1, max_length=50)
    story_security: str = Field(min_length=1, max_length=50)
    allowed_classics_authors: list[str] | None = Field(default=None)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    register_account(db, payload.email, payload.password)
    return {"status": "account_created"}


@router.post("/auth/login")
def login(
    payload: LoginRequest,
    request: Request,
    _: None = Depends(login_rate_limit),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    account = authenticate_account(db, payload.email, payload.password)
    access_token = create_access_token(account.account_id, account.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/auth/reset-request")
def reset_request(
    payload: ResetRequest,
    request: Request,
    _: None = Depends(reset_rate_limit),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    create_password_reset_token(db, payload.email)
    return {"status": "reset_email_sent"}


@router.post("/auth/reset-confirm")
def reset_confirm(
    payload: ResetConfirmRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    reset_password_with_token(db, payload.reset_token, payload.new_password)
    return {"status": "password_updated"}


@router.get("/accounts/me", response_model=AccountProfileResponse)
def get_me(current_account=Depends(get_current_account), db: Session = Depends(get_db)):
    return get_account_profile(db, current_account.account_id)


@router.put("/accounts/me", response_model=AccountProfileResponse)
def update_me(
    payload: AccountUpdateRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return update_account_profile(
        db,
        current_account.account_id,
        payload.subscription_level,
        payload.story_security,
        payload.allowed_classics_authors,
    )
