from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Float, Integer, MetaData, String, Table, TIMESTAMP, and_, desc, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

accounts_table = Table(
    "accounts",
    metadata,
    Column("account_id", Integer, primary_key=True),
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
    game_result_id: int
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


@dataclass
class StoryRecord:
    story_id: int
    title: str | None
    trait_focus: str | None
    created_at: datetime | None
    updated_at: datetime | None


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


def _to_progress(row, reader_id: int) -> ReaderProgressRecord:
    if row is None:
        return ReaderProgressRecord(
            reader_id=reader_id,
            stories_read=0,
            words_mastered=0,
            reading_speed=None,
            preferred_themes=None,
            traits_reinforced=None,
        )
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
        game_result_id=row.game_result_id,
        game_type=row.game_type,
        difficulty_level=row.difficulty_level,
        score=row.score,
        duration_seconds=row.duration_seconds,
        played_at=row.played_at,
    )


def _to_story(row) -> StoryRecord | None:
    if row is None:
        return None
    return StoryRecord(
        story_id=row.story_id,
        title=row.title,
        trait_focus=row.trait_focus,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def account_exists(db: Session, account_id: int) -> bool:
    row = db.execute(
        select(accounts_table.c.account_id).where(accounts_table.c.account_id == account_id)
    ).first()
    return row is not None


def get_account_reader(db: Session, account_id: int, reader_id: int) -> ReaderRecord | None:
    row = db.execute(
        select(readers_table).where(
            and_(
                readers_table.c.account_id == account_id,
                readers_table.c.reader_id == reader_id,
            )
        )
    ).mappings().first()
    return _to_reader(row)


def list_account_readers(db: Session, account_id: int) -> list[ReaderRecord]:
    rows = db.execute(
        select(readers_table)
        .where(readers_table.c.account_id == account_id)
        .order_by(readers_table.c.reader_id.asc())
    ).mappings().all()
    return [_to_reader(row) for row in rows if _to_reader(row) is not None]


def get_reader_progress(db: Session, reader_id: int) -> ReaderProgressRecord:
    row = db.execute(
        select(reader_progress_table).where(reader_progress_table.c.reader_id == reader_id)
    ).mappings().first()
    return _to_progress(row, reader_id)


def list_reader_vocabulary_progress(
    db: Session,
    reader_id: int,
    limit: int | None = None,
) -> list[VocabularyProgressRecord]:
    query = (
        select(
            vocabulary_table.c.word_id,
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
            desc(reader_vocabulary_progress_table.c.last_seen),
            vocabulary_table.c.word.asc(),
        )
    )
    if limit is not None:
        query = query.limit(limit)

    rows = db.execute(query).mappings().all()
    return [_to_vocabulary_progress(row) for row in rows if _to_vocabulary_progress(row) is not None]


def list_reader_game_results(
    db: Session,
    reader_id: int,
    limit: int = 50,
) -> list[GameResultRecord]:
    rows = db.execute(
        select(game_results_table)
        .where(game_results_table.c.reader_id == reader_id)
        .order_by(desc(game_results_table.c.played_at), desc(game_results_table.c.game_result_id))
        .limit(limit)
    ).mappings().all()
    return [_to_game_result(row) for row in rows if _to_game_result(row) is not None]


def list_reader_stories(
    db: Session,
    reader_id: int,
    limit: int = 10,
) -> list[StoryRecord]:
    rows = db.execute(
        select(
            stories_generated_table.c.story_id,
            stories_generated_table.c.title,
            stories_generated_table.c.trait_focus,
            stories_generated_table.c.created_at,
            stories_generated_table.c.updated_at,
        )
        .where(stories_generated_table.c.reader_id == reader_id)
        .order_by(desc(stories_generated_table.c.updated_at), desc(stories_generated_table.c.story_id))
        .limit(limit)
    ).mappings().all()
    return [_to_story(row) for row in rows if _to_story(row) is not None]
