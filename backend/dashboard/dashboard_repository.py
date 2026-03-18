from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, and_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

accounts_table = Table(
    "accounts",
    metadata,
    Column("account_id", Integer, primary_key=True),
    Column("email", String(255)),
    Column("password_hash", String(255)),
    Column("subscription_level", String(50)),
    Column("story_security", String(50)),
    Column("created_at", TIMESTAMP),
)

readers_table = Table(
    "readers",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("name", String(100)),
    Column("age", Integer),
    Column("reading_level", String(50)),
    Column("gender_preference", String(50)),
    Column("trait_focus", JSON),
    Column("created_at", TIMESTAMP),
)

stories_generated_table = Table(
    "stories_generated",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("reader_world_id", Integer),
    Column("title", String(255)),
    Column("trait_focus", String(100)),
    Column("current_version", Integer),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

game_results_table = Table(
    "game_results",
    metadata,
    Column("game_result_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("game_type", String(50)),
    Column("difficulty_level", Integer),
    Column("score", Integer),
    Column("duration_seconds", Integer),
    Column("played_at", TIMESTAMP),
)


@dataclass
class ReaderRecord:
    reader_id: int
    account_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    gender_preference: str | None
    trait_focus: object
    created_at: datetime | None


@dataclass
class StoryHistoryRecord:
    story_id: int
    title: str | None
    trait_focus: str | None
    created_at: datetime | None


@dataclass
class GameResultRecord:
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


def _to_reader(row) -> ReaderRecord | None:
    if row is None:
        return None
    return ReaderRecord(
        reader_id=row.reader_id,
        account_id=row.account_id,
        name=row.name,
        age=row.age,
        reading_level=row.reading_level,
        gender_preference=row.gender_preference,
        trait_focus=row.trait_focus,
        created_at=row.created_at,
    )


def _to_story_history(row) -> StoryHistoryRecord | None:
    if row is None:
        return None
    return StoryHistoryRecord(
        story_id=row.story_id,
        title=row.title,
        trait_focus=row.trait_focus,
        created_at=row.created_at,
    )


def _to_game_result(row) -> GameResultRecord | None:
    if row is None:
        return None
    return GameResultRecord(
        game_type=row.game_type,
        difficulty_level=row.difficulty_level,
        score=row.score,
        duration_seconds=row.duration_seconds,
        played_at=row.played_at,
    )


def get_account(account_id: int, db: Session) -> None:
    row = db.execute(
        select(accounts_table.c.account_id).where(accounts_table.c.account_id == account_id)
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )


def list_account_readers(db: Session, account_id: int) -> list[ReaderRecord]:
    rows = db.execute(
        select(readers_table)
        .where(readers_table.c.account_id == account_id)
        .order_by(readers_table.c.reader_id.asc())
    ).mappings().all()
    return [_to_reader(row) for row in rows]


def get_account_reader(db: Session, account_id: int, reader_id: int) -> ReaderRecord:
    row = db.execute(
        select(readers_table).where(
            and_(
                readers_table.c.account_id == account_id,
                readers_table.c.reader_id == reader_id,
            )
        )
    ).mappings().first()
    reader = _to_reader(row)
    if reader is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )
    return reader


def list_reader_stories(db: Session, reader_id: int) -> list[StoryHistoryRecord]:
    rows = db.execute(
        select(
            stories_generated_table.c.story_id,
            stories_generated_table.c.title,
            stories_generated_table.c.trait_focus,
            stories_generated_table.c.created_at,
        )
        .where(stories_generated_table.c.reader_id == reader_id)
        .order_by(stories_generated_table.c.created_at.desc(), stories_generated_table.c.story_id.desc())
    ).mappings().all()
    return [_to_story_history(row) for row in rows]


def list_reader_game_results(db: Session, reader_id: int) -> list[GameResultRecord]:
    rows = db.execute(
        select(
            game_results_table.c.game_type,
            game_results_table.c.difficulty_level,
            game_results_table.c.score,
            game_results_table.c.duration_seconds,
            game_results_table.c.played_at,
        )
        .where(game_results_table.c.reader_id == reader_id)
        .order_by(game_results_table.c.played_at.desc(), game_results_table.c.game_result_id.desc())
    ).mappings().all()
    return [_to_game_result(row) for row in rows]
