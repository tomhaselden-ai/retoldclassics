from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.rate_limit import build_rate_limit_dependency
from backend.auth.token_manager import get_current_account
from backend.config.settings import RATE_LIMIT_LOGIN_REQUESTS, RATE_LIMIT_LOGIN_WINDOW_SECONDS
from backend.db.database import get_db
from backend.parent_pin.pin_service import (
    ParentPinError,
    clear_parent_pin_session,
    get_parent_pin_status,
    set_parent_pin,
    verify_parent_pin,
)


router = APIRouter(prefix="/parent/pin", tags=["parent-pin"])
pin_verify_rate_limit = build_rate_limit_dependency(
    "parent_pin_verify",
    RATE_LIMIT_LOGIN_REQUESTS,
    RATE_LIMIT_LOGIN_WINDOW_SECONDS,
)


class ParentPinStatusResponse(BaseModel):
    pin_enabled: bool
    verified: bool
    locked_until: str | None
    attempts_remaining: int
    session_expires_at: str | None


class ParentPinSetRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=8)


class ParentPinVerifyRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=8)


class ParentPinSessionResponse(ParentPinStatusResponse):
    status: str
    session_token: str


class ParentPinClearResponse(BaseModel):
    status: str


def _error_response(exc: ParentPinError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/status", response_model=ParentPinStatusResponse)
def get_parent_pin_status_route(
    current_account=Depends(get_current_account),
    parent_pin_session_token: str | None = Header(default=None, alias="X-Parent-Pin-Session"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_parent_pin_status(db, current_account.account_id, parent_pin_session_token)
    except ParentPinError as exc:
        return _error_response(exc)


@router.post("/set", response_model=ParentPinSessionResponse)
def set_parent_pin_route(
    payload: ParentPinSetRequest,
    current_account=Depends(get_current_account),
    parent_pin_session_token: str | None = Header(default=None, alias="X-Parent-Pin-Session"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return set_parent_pin(db, current_account.account_id, payload.pin, parent_pin_session_token)
    except ParentPinError as exc:
        return _error_response(exc)


@router.post("/verify", response_model=ParentPinSessionResponse)
def verify_parent_pin_route(
    payload: ParentPinVerifyRequest,
    _: None = Depends(pin_verify_rate_limit),
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return verify_parent_pin(db, current_account.account_id, payload.pin)
    except ParentPinError as exc:
        return _error_response(exc)


@router.delete("/session", response_model=ParentPinClearResponse)
def clear_parent_pin_session_route(
    current_account=Depends(get_current_account),
    parent_pin_session_token: str | None = Header(default=None, alias="X-Parent-Pin-Session"),
    db: Session = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    try:
        return clear_parent_pin_session(db, current_account.account_id, parent_pin_session_token)
    except ParentPinError as exc:
        return _error_response(exc)
