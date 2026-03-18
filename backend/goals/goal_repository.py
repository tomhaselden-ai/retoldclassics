from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.orm import Session


metadata = MetaData()

reader_goals_table = Table(
    "reader_goals",
    metadata,
    Column("goal_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("reader_id", Integer, nullable=False),
    Column("goal_type", String(50), nullable=False),
    Column("title", String(255), nullable=False),
    Column("target_value", Integer, nullable=False),
    Column("is_active", Boolean, nullable=False),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

reader_goal_progress_table = Table(
    "reader_goal_progress",
    metadata,
    Column("progress_id", Integer, primary_key=True),
    Column("goal_id", Integer, nullable=False),
    Column("reader_id", Integer, nullable=False),
    Column("current_value", Integer, nullable=False),
    Column("target_value", Integer, nullable=False),
    Column("progress_percent", Integer, nullable=False),
    Column("status", String(20), nullable=False),
    Column("updated_at", TIMESTAMP),
    Column("completed_at", TIMESTAMP),
)


@dataclass
class ReaderGoalRecord:
    goal_id: int
    account_id: int
    reader_id: int
    goal_type: str
    title: str
    target_value: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class ReaderGoalProgressRecord:
    progress_id: int
    goal_id: int
    reader_id: int
    current_value: int
    target_value: int
    progress_percent: int
    status: str
    updated_at: datetime | None
    completed_at: datetime | None


def _to_goal(row) -> ReaderGoalRecord | None:
    if row is None:
        return None
    return ReaderGoalRecord(
        goal_id=row.goal_id,
        account_id=row.account_id,
        reader_id=row.reader_id,
        goal_type=row.goal_type,
        title=row.title,
        target_value=row.target_value,
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_progress(row) -> ReaderGoalProgressRecord | None:
    if row is None:
        return None
    return ReaderGoalProgressRecord(
        progress_id=row.progress_id,
        goal_id=row.goal_id,
        reader_id=row.reader_id,
        current_value=row.current_value,
        target_value=row.target_value,
        progress_percent=row.progress_percent,
        status=row.status,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def list_goals_for_account(db: Session, account_id: int) -> list[ReaderGoalRecord]:
    rows = db.execute(
        select(reader_goals_table)
        .where(reader_goals_table.c.account_id == account_id)
        .order_by(reader_goals_table.c.reader_id.asc(), reader_goals_table.c.goal_id.asc())
    ).mappings().all()
    return [_to_goal(row) for row in rows]


def list_goals_for_reader(db: Session, account_id: int, reader_id: int) -> list[ReaderGoalRecord]:
    rows = db.execute(
        select(reader_goals_table)
        .where(reader_goals_table.c.account_id == account_id)
        .where(reader_goals_table.c.reader_id == reader_id)
        .order_by(reader_goals_table.c.goal_id.asc())
    ).mappings().all()
    return [_to_goal(row) for row in rows]


def get_goal_for_account(db: Session, account_id: int, goal_id: int) -> ReaderGoalRecord | None:
    row = db.execute(
        select(reader_goals_table)
        .where(reader_goals_table.c.account_id == account_id)
        .where(reader_goals_table.c.goal_id == goal_id)
    ).mappings().first()
    return _to_goal(row)


def insert_goal(
    db: Session,
    account_id: int,
    reader_id: int,
    goal_type: str,
    title: str,
    target_value: int,
) -> int:
    result = db.execute(
        reader_goals_table.insert().values(
            account_id=account_id,
            reader_id=reader_id,
            goal_type=goal_type,
            title=title,
            target_value=target_value,
            is_active=True,
        )
    )
    return int(result.inserted_primary_key[0])


def update_goal_record(
    db: Session,
    goal_id: int,
    *,
    title: str,
    target_value: int,
    is_active: bool,
) -> None:
    db.execute(
        reader_goals_table.update()
        .where(reader_goals_table.c.goal_id == goal_id)
        .values(title=title, target_value=target_value, is_active=is_active)
    )


def get_progress_for_goal(db: Session, goal_id: int) -> ReaderGoalProgressRecord | None:
    row = db.execute(
        select(reader_goal_progress_table).where(reader_goal_progress_table.c.goal_id == goal_id)
    ).mappings().first()
    return _to_progress(row)


def upsert_goal_progress(
    db: Session,
    *,
    goal_id: int,
    reader_id: int,
    current_value: int,
    target_value: int,
    progress_percent: int,
    status: str,
    completed_at: datetime | None,
) -> None:
    existing = get_progress_for_goal(db, goal_id)
    if existing is None:
        db.execute(
            reader_goal_progress_table.insert().values(
                goal_id=goal_id,
                reader_id=reader_id,
                current_value=current_value,
                target_value=target_value,
                progress_percent=progress_percent,
                status=status,
                completed_at=completed_at,
            )
        )
        return

    db.execute(
        reader_goal_progress_table.update()
        .where(reader_goal_progress_table.c.goal_id == goal_id)
        .values(
            current_value=current_value,
            target_value=target_value,
            progress_percent=progress_percent,
            status=status,
            completed_at=completed_at,
        )
    )
