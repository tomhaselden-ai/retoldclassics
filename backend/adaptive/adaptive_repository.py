from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, TIMESTAMP, and_, desc, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

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

reader_progress_table = Table(
    "reader_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("stories_read", Integer),
    Column("words_mastered", Integer),
    Column("reading_speed", Float),
    Column("preferred_themes", JSON),
    Column("traits_reinforced", JSON),
)

reader_vocabulary_progress_table = Table(
    "reader_vocabulary_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("word_id", Integer, primary_key=True),
    Column("mastery_level", Integer),
    Column("last_seen", TIMESTAMP),
)

vocabulary_table = Table(
    "vocabulary",
    metadata,
    Column("word_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("word", String(100)),
    Column("difficulty_level", Integer),
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
class ReaderProgressRecord:
    reader_id: int
    stories_read: int | None
    words_mastered: int | None
    reading_speed: float | None
    preferred_themes: object
    traits_reinforced: object


@dataclass
class VocabularyProgressRecord:
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


@dataclass
class GameResultRecord:
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


def _to_reader_progress(row) -> ReaderProgressRecord | None:
    if row is None:
        return None
    return ReaderProgressRecord(
        reader_id=row.reader_id,
        stories_read=row.stories_read,
        words_mastered=row.words_mastered,
        reading_speed=row.reading_speed,
        preferred_themes=row.preferred_themes,
        traits_reinforced=row.traits_reinforced,
    )


def _to_vocabulary_progress(row) -> VocabularyProgressRecord | None:
    if row is None:
        return None
    return VocabularyProgressRecord(
        word_id=row.word_id,
        word=row.word,
        difficulty_level=row.difficulty_level,
        mastery_level=row.mastery_level,
        last_seen=row.last_seen,
    )


def _to_game_result(row) -> GameResultRecord | None:
    if row is None:
        return None
    return GameResultRecord(
        difficulty_level=row.difficulty_level,
        score=row.score,
        duration_seconds=row.duration_seconds,
        played_at=row.played_at,
    )


def get_reader_for_account(db: Session, account_id: int, reader_id: int) -> ReaderRecord:
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


def get_reader_progress(db: Session, reader_id: int) -> ReaderProgressRecord:
    row = db.execute(
        select(reader_progress_table).where(reader_progress_table.c.reader_id == reader_id)
    ).mappings().first()
    progress = _to_reader_progress(row)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing progress data",
        )
    return progress


def list_reader_vocabulary_progress(db: Session, reader_id: int) -> list[VocabularyProgressRecord]:
    rows = db.execute(
        select(
            reader_vocabulary_progress_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.difficulty_level,
            reader_vocabulary_progress_table.c.mastery_level,
            reader_vocabulary_progress_table.c.last_seen,
        )
        .select_from(
            reader_vocabulary_progress_table.join(
                vocabulary_table,
                reader_vocabulary_progress_table.c.word_id == vocabulary_table.c.word_id,
            )
        )
        .where(reader_vocabulary_progress_table.c.reader_id == reader_id)
        .order_by(
            reader_vocabulary_progress_table.c.mastery_level.asc(),
            desc(reader_vocabulary_progress_table.c.last_seen),
        )
    ).mappings().all()
    vocabulary_rows = [_to_vocabulary_progress(row) for row in rows]
    if not vocabulary_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing vocabulary records",
        )
    return vocabulary_rows


def list_recent_game_results(db: Session, reader_id: int, limit: int = 10) -> list[GameResultRecord]:
    rows = db.execute(
        select(
            game_results_table.c.difficulty_level,
            game_results_table.c.score,
            game_results_table.c.duration_seconds,
            game_results_table.c.played_at,
        )
        .where(game_results_table.c.reader_id == reader_id)
        .order_by(desc(game_results_table.c.played_at), desc(game_results_table.c.game_result_id))
        .limit(limit)
    ).mappings().all()
    return [_to_game_result(row) for row in rows]
