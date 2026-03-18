import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.auth.auth_service import pwd_context
from backend.parent_pin.pin_repository import (
    ParentPinSessionRecord,
    ParentPinStateRecord,
    create_parent_pin_session,
    get_parent_pin_session,
    get_parent_pin_state,
    revoke_parent_pin_session,
    update_parent_pin_state,
)


PARENT_PIN_PATTERN = re.compile(r"^\d{4,8}$")
PARENT_PIN_MAX_FAILED_ATTEMPTS = 5
PARENT_PIN_LOCKOUT_MINUTES = 15
PARENT_PIN_SESSION_HOURS = 12


class ParentPinError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_lockout(locked_until: datetime | None) -> datetime | None:
    if locked_until is None:
        return None
    if locked_until.tzinfo is None:
        return locked_until.replace(tzinfo=timezone.utc)
    return locked_until.astimezone(timezone.utc)


def _is_locked(state: ParentPinStateRecord, now: datetime) -> bool:
    locked_until = _normalize_lockout(state.parent_pin_locked_until)
    return locked_until is not None and locked_until > now


def _validate_pin(pin: str) -> str:
    normalized = pin.strip()
    if not PARENT_PIN_PATTERN.fullmatch(normalized):
        raise ParentPinError("invalid_parent_pin_format", 400)
    return normalized


def hash_parent_pin(pin: str) -> str:
    return pwd_context.hash(_validate_pin(pin))


def _verify_parent_pin(pin: str, parent_pin_hash: str) -> bool:
    return pwd_context.verify(_validate_pin(pin), parent_pin_hash)


def _build_status_payload(
    state: ParentPinStateRecord,
    session: ParentPinSessionRecord | None,
    *,
    now: datetime,
) -> dict[str, object]:
    locked_until = _normalize_lockout(state.parent_pin_locked_until)
    is_verified = session is not None and session.revoked_at is None and session.expires_at is not None
    session_expires_at = None
    if is_verified and session.expires_at is not None:
        expiry = _normalize_lockout(session.expires_at)
        if expiry is not None and expiry > now:
            session_expires_at = expiry.isoformat()
        else:
            is_verified = False

    return {
        "pin_enabled": bool(state.parent_pin_enabled),
        "verified": is_verified,
        "locked_until": locked_until.isoformat() if locked_until and locked_until > now else None,
        "attempts_remaining": max(0, PARENT_PIN_MAX_FAILED_ATTEMPTS - state.failed_pin_attempts),
        "session_expires_at": session_expires_at,
    }


def _get_valid_parent_pin_session(
    db: Session,
    account_id: int,
    session_token: str | None,
    *,
    now: datetime,
) -> ParentPinSessionRecord | None:
    if not isinstance(session_token, str) or not session_token.strip():
        return None

    session = get_parent_pin_session(db, account_id, session_token.strip())
    if session is None or session.revoked_at is not None:
        return None

    expires_at = _normalize_lockout(session.expires_at)
    if expires_at is None or expires_at <= now:
        return None
    return session


def get_parent_pin_status(db: Session, account_id: int, session_token: str | None = None) -> dict[str, object]:
    now = _utcnow()
    state = get_parent_pin_state(db, account_id)
    if state is None:
        raise ParentPinError("account_not_found", 404)

    session = _get_valid_parent_pin_session(db, account_id, session_token, now=now)
    return _build_status_payload(state, session, now=now)


def set_parent_pin(
    db: Session,
    account_id: int,
    pin: str,
    session_token: str | None = None,
) -> dict[str, object]:
    now = _utcnow()
    state = get_parent_pin_state(db, account_id)
    if state is None:
        raise ParentPinError("account_not_found", 404)

    valid_session = _get_valid_parent_pin_session(db, account_id, session_token, now=now)
    if state.parent_pin_enabled and valid_session is None:
        raise ParentPinError("parent_pin_verification_required", 403)

    try:
        pin_hash = hash_parent_pin(pin)
        update_parent_pin_state(
            db,
            account_id,
            parent_pin_hash=pin_hash,
            parent_pin_enabled=True,
            failed_pin_attempts=0,
            parent_pin_locked_until=None,
        )
        session_token_value = secrets.token_urlsafe(32)
        session_expires_at = now + timedelta(hours=PARENT_PIN_SESSION_HOURS)
        create_parent_pin_session(db, account_id, session_token_value, session_expires_at)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ParentPinError("database_failure", 500) from exc

    refreshed = get_parent_pin_state(db, account_id)
    if refreshed is None:
        raise ParentPinError("account_not_found", 404)
    payload = _build_status_payload(
        refreshed,
        ParentPinSessionRecord(
            session_id=0,
            account_id=account_id,
            session_token=session_token_value,
            created_at=now,
            expires_at=session_expires_at,
            revoked_at=None,
        ),
        now=now,
    )
    payload["status"] = "pin_set"
    payload["session_token"] = session_token_value
    return payload


def verify_parent_pin(db: Session, account_id: int, pin: str) -> dict[str, object]:
    now = _utcnow()
    state = get_parent_pin_state(db, account_id)
    if state is None:
        raise ParentPinError("account_not_found", 404)
    if not state.parent_pin_enabled or not state.parent_pin_hash:
        raise ParentPinError("parent_pin_not_set", 404)
    if _is_locked(state, now):
        raise ParentPinError("parent_pin_locked", 423)

    try:
        if not _verify_parent_pin(pin, state.parent_pin_hash):
            failed_attempts = state.failed_pin_attempts + 1
            locked_until = None
            error_code = "invalid_parent_pin"
            status_code = 401
            if failed_attempts >= PARENT_PIN_MAX_FAILED_ATTEMPTS:
                failed_attempts = PARENT_PIN_MAX_FAILED_ATTEMPTS
                locked_until = now + timedelta(minutes=PARENT_PIN_LOCKOUT_MINUTES)
                error_code = "parent_pin_locked"
                status_code = 423

            update_parent_pin_state(
                db,
                account_id,
                parent_pin_hash=state.parent_pin_hash,
                parent_pin_enabled=True,
                failed_pin_attempts=failed_attempts,
                parent_pin_locked_until=locked_until,
            )
            db.commit()
            raise ParentPinError(error_code, status_code)

        update_parent_pin_state(
            db,
            account_id,
            parent_pin_hash=state.parent_pin_hash,
            parent_pin_enabled=True,
            failed_pin_attempts=0,
            parent_pin_locked_until=None,
        )
        session_token_value = secrets.token_urlsafe(32)
        session_expires_at = now + timedelta(hours=PARENT_PIN_SESSION_HOURS)
        create_parent_pin_session(db, account_id, session_token_value, session_expires_at)
        db.commit()
    except ParentPinError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise ParentPinError("database_failure", 500) from exc

    refreshed = get_parent_pin_state(db, account_id)
    if refreshed is None:
        raise ParentPinError("account_not_found", 404)
    payload = _build_status_payload(
        refreshed,
        ParentPinSessionRecord(
            session_id=0,
            account_id=account_id,
            session_token=session_token_value,
            created_at=now,
            expires_at=session_expires_at,
            revoked_at=None,
        ),
        now=now,
    )
    payload["status"] = "verified"
    payload["session_token"] = session_token_value
    return payload


def clear_parent_pin_session(db: Session, account_id: int, session_token: str | None) -> dict[str, str]:
    if not isinstance(session_token, str) or not session_token.strip():
        raise ParentPinError("parent_pin_session_required", 400)

    try:
        revoke_parent_pin_session(db, account_id, session_token.strip(), _utcnow())
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ParentPinError("database_failure", 500) from exc

    return {"status": "cleared"}
