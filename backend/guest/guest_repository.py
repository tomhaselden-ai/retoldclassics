from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, TIMESTAMP, func, insert, select, update
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

guest_sessions_table = Table(
    "guest_sessions",
    metadata,
    Column("session_id", Integer, primary_key=True),
    Column("session_token", String(96), nullable=False),
    Column("last_ip", String(64)),
    Column("created_at", TIMESTAMP),
    Column("last_seen_at", TIMESTAMP),
    Column("expires_at", TIMESTAMP),
)

guest_usage_events_table = Table(
    "guest_usage_events",
    metadata,
    Column("event_id", Integer, primary_key=True),
    Column("session_id", Integer, ForeignKey("guest_sessions.session_id", ondelete="CASCADE"), nullable=False),
    Column("event_type", String(50), nullable=False),
    Column("story_id", Integer, nullable=True),
    Column("metadata_json", JSON),
    Column("created_at", TIMESTAMP),
)


@dataclass
class GuestSessionRecord:
    session_id: int
    session_token: str
    last_ip: str | None
    created_at: datetime | None
    last_seen_at: datetime | None
    expires_at: datetime | None


def _to_guest_session(row: Any) -> GuestSessionRecord | None:
    if row is None:
        return None
    return GuestSessionRecord(
        session_id=row.session_id,
        session_token=row.session_token,
        last_ip=row.last_ip,
        created_at=row.created_at,
        last_seen_at=row.last_seen_at,
        expires_at=row.expires_at,
    )


def get_guest_session_by_token(db: Session, session_token: str) -> GuestSessionRecord | None:
    row = db.execute(
        select(guest_sessions_table).where(guest_sessions_table.c.session_token == session_token)
    ).mappings().first()
    return _to_guest_session(row)


def create_guest_session(
    db: Session,
    session_token: str,
    last_ip: str | None,
    expires_at: datetime,
) -> GuestSessionRecord:
    result = db.execute(
        insert(guest_sessions_table).values(
            session_token=session_token,
            last_ip=last_ip,
            last_seen_at=func.now(),
            expires_at=expires_at,
        )
    )
    session_id = int(result.lastrowid)
    return GuestSessionRecord(
        session_id=session_id,
        session_token=session_token,
        last_ip=last_ip,
        created_at=None,
        last_seen_at=None,
        expires_at=expires_at,
    )


def touch_guest_session(db: Session, session_id: int, last_ip: str | None, expires_at: datetime) -> None:
    values: dict[str, Any] = {
        "last_seen_at": func.now(),
        "expires_at": expires_at,
    }
    if last_ip:
        values["last_ip"] = last_ip
    db.execute(
        update(guest_sessions_table)
        .where(guest_sessions_table.c.session_id == session_id)
        .values(**values)
    )


def count_guest_classic_reads(db: Session, session_id: int) -> int:
    value = db.execute(
        select(func.count(func.distinct(guest_usage_events_table.c.story_id))).where(
            guest_usage_events_table.c.session_id == session_id,
            guest_usage_events_table.c.event_type == "classic_read",
            guest_usage_events_table.c.story_id.is_not(None),
        )
    ).scalar_one()
    return int(value or 0)


def has_guest_classic_read(db: Session, session_id: int, story_id: int) -> bool:
    row = db.execute(
        select(guest_usage_events_table.c.event_id).where(
            guest_usage_events_table.c.session_id == session_id,
            guest_usage_events_table.c.event_type == "classic_read",
            guest_usage_events_table.c.story_id == story_id,
        )
    ).first()
    return row is not None


def count_guest_game_launches(db: Session, session_id: int) -> int:
    value = db.execute(
        select(func.count()).where(
            guest_usage_events_table.c.session_id == session_id,
            guest_usage_events_table.c.event_type == "game_launch",
        )
    ).scalar_one()
    return int(value or 0)


def insert_guest_usage_event(
    db: Session,
    session_id: int,
    event_type: str,
    story_id: int | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> None:
    db.execute(
        insert(guest_usage_events_table).values(
            session_id=session_id,
            event_type=event_type,
            story_id=story_id,
            metadata_json=metadata_json,
        )
    )
