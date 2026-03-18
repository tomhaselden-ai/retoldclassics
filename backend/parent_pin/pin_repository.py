from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, TIMESTAMP, insert, select, update
from sqlalchemy.orm import Session

from backend.auth.auth_service import accounts_table


metadata = MetaData()

parent_pin_sessions_table = Table(
    "parent_pin_sessions",
    metadata,
    Column("session_id", Integer, primary_key=True),
    Column("account_id", Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False),
    Column("session_token", String(96), nullable=False),
    Column("created_at", TIMESTAMP),
    Column("expires_at", TIMESTAMP),
    Column("revoked_at", TIMESTAMP),
)


@dataclass
class ParentPinStateRecord:
    account_id: int
    parent_pin_hash: str | None
    parent_pin_enabled: bool
    failed_pin_attempts: int
    parent_pin_locked_until: datetime | None


@dataclass
class ParentPinSessionRecord:
    session_id: int
    account_id: int
    session_token: str
    created_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None


def get_parent_pin_state(db: Session, account_id: int) -> ParentPinStateRecord | None:
    row = db.execute(
        select(
            accounts_table.c.account_id,
            accounts_table.c.parent_pin_hash,
            accounts_table.c.parent_pin_enabled,
            accounts_table.c.failed_pin_attempts,
            accounts_table.c.parent_pin_locked_until,
        ).where(accounts_table.c.account_id == account_id)
    ).mappings().first()
    if row is None:
        return None
    return ParentPinStateRecord(
        account_id=row["account_id"],
        parent_pin_hash=row["parent_pin_hash"],
        parent_pin_enabled=bool(row["parent_pin_enabled"]),
        failed_pin_attempts=int(row["failed_pin_attempts"] or 0),
        parent_pin_locked_until=row["parent_pin_locked_until"],
    )


def update_parent_pin_state(
    db: Session,
    account_id: int,
    *,
    parent_pin_hash: str | None,
    parent_pin_enabled: bool,
    failed_pin_attempts: int,
    parent_pin_locked_until: datetime | None,
) -> None:
    db.execute(
        update(accounts_table)
        .where(accounts_table.c.account_id == account_id)
        .values(
            parent_pin_hash=parent_pin_hash,
            parent_pin_enabled=1 if parent_pin_enabled else 0,
            failed_pin_attempts=failed_pin_attempts,
            parent_pin_locked_until=parent_pin_locked_until,
        )
    )


def create_parent_pin_session(
    db: Session,
    account_id: int,
    session_token: str,
    expires_at: datetime,
) -> ParentPinSessionRecord:
    result = db.execute(
        insert(parent_pin_sessions_table).values(
            account_id=account_id,
            session_token=session_token,
            expires_at=expires_at,
        )
    )
    return ParentPinSessionRecord(
        session_id=int(result.lastrowid),
        account_id=account_id,
        session_token=session_token,
        created_at=None,
        expires_at=expires_at,
        revoked_at=None,
    )


def get_parent_pin_session(
    db: Session,
    account_id: int,
    session_token: str,
) -> ParentPinSessionRecord | None:
    row = db.execute(
        select(parent_pin_sessions_table).where(
            parent_pin_sessions_table.c.account_id == account_id,
            parent_pin_sessions_table.c.session_token == session_token,
        )
    ).mappings().first()
    if row is None:
        return None
    return ParentPinSessionRecord(
        session_id=row["session_id"],
        account_id=row["account_id"],
        session_token=row["session_token"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
    )


def revoke_parent_pin_session(db: Session, account_id: int, session_token: str, revoked_at: datetime) -> None:
    db.execute(
        update(parent_pin_sessions_table)
        .where(
            parent_pin_sessions_table.c.account_id == account_id,
            parent_pin_sessions_table.c.session_token == session_token,
        )
        .values(revoked_at=revoked_at)
    )
