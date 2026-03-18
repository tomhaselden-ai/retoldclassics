from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    desc,
    func,
    literal,
    or_,
    select,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

reader_vocabulary_progress_table = Table(
    "reader_vocabulary_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("word_id", Integer, primary_key=True),
    Column("mastery_level", Integer),
    Column("last_seen", DateTime),
)

stories_generated_table = Table(
    "stories_generated",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("title", String(255)),
    Column("trait_focus", String(100)),
    Column("created_at", DateTime),
)

vocabulary_table = Table(
    "vocabulary",
    metadata,
    Column("word_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("word", String(100)),
    Column("difficulty_level", Integer),
    Column("definition", Text),
    Column("example_sentence", Text),
)

game_sessions_table = Table(
    "game_sessions",
    metadata,
    Column("session_id", Integer, primary_key=True),
    Column("account_id", Integer),
    Column("reader_id", Integer),
    Column("game_type", String(50)),
    Column("source_type", String(50)),
    Column("source_story_id", Integer),
    Column("difficulty_level", Integer),
    Column("status", String(20)),
    Column("item_count", Integer),
    Column("words_attempted", Integer),
    Column("words_correct", Integer),
    Column("words_incorrect", Integer),
    Column("hints_used", Integer),
    Column("completion_status", String(20)),
    Column("started_at", DateTime),
    Column("ended_at", DateTime),
    Column("duration_seconds", Integer),
    Column("session_payload", JSON),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

game_word_attempts_table = Table(
    "game_word_attempts",
    metadata,
    Column("attempt_id", Integer, primary_key=True),
    Column("session_id", Integer),
    Column("word_id", Integer),
    Column("word_text", String(100)),
    Column("game_type", String(50)),
    Column("attempt_count", Integer),
    Column("correct", Boolean),
    Column("time_spent_seconds", Integer),
    Column("hint_used", Boolean),
    Column("skipped", Boolean),
    Column("created_at", DateTime),
)


@dataclass
class GameSessionWordItemRecord:
    word_id: int | None
    word: str | None
    definition: str | None
    example_sentence: str | None
    difficulty_level: int | None
    reader_id: int
    story_id: int | None
    source_type: str
    trait_focus: str | None


@dataclass
class GameSessionRecord:
    session_id: int
    account_id: int
    reader_id: int
    game_type: str
    source_type: str
    source_story_id: int | None
    difficulty_level: int
    status: str
    item_count: int
    words_attempted: int
    words_correct: int
    words_incorrect: int
    hints_used: int
    completion_status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    session_payload: dict | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class GameWordAttemptRecord:
    attempt_id: int
    session_id: int
    word_id: int | None
    word_text: str
    game_type: str
    attempt_count: int
    correct: bool
    time_spent_seconds: int
    hint_used: bool
    skipped: bool
    created_at: datetime | None


def _to_word_item(row) -> GameSessionWordItemRecord | None:
    if row is None:
        return None
    return GameSessionWordItemRecord(
        word_id=row.word_id,
        word=row.word,
        definition=row.definition,
        example_sentence=row.example_sentence,
        difficulty_level=row.difficulty_level,
        reader_id=row.reader_id,
        story_id=row.story_id,
        source_type=row.source_type,
        trait_focus=row.trait_focus,
    )


def _to_session(row) -> GameSessionRecord | None:
    if row is None:
        return None
    return GameSessionRecord(
        session_id=row.session_id,
        account_id=row.account_id,
        reader_id=row.reader_id,
        game_type=row.game_type,
        source_type=row.source_type,
        source_story_id=row.source_story_id,
        difficulty_level=row.difficulty_level,
        status=row.status,
        item_count=row.item_count,
        words_attempted=row.words_attempted,
        words_correct=row.words_correct,
        words_incorrect=row.words_incorrect,
        hints_used=row.hints_used,
        completion_status=row.completion_status,
        started_at=row.started_at,
        ended_at=row.ended_at,
        duration_seconds=row.duration_seconds,
        session_payload=row.session_payload if isinstance(row.session_payload, dict) else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_word_attempt(row) -> GameWordAttemptRecord | None:
    if row is None:
        return None
    return GameWordAttemptRecord(
        attempt_id=row.attempt_id,
        session_id=row.session_id,
        word_id=row.word_id,
        word_text=row.word_text,
        game_type=row.game_type,
        attempt_count=row.attempt_count,
        correct=bool(row.correct),
        time_spent_seconds=row.time_spent_seconds,
        hint_used=bool(row.hint_used),
        skipped=bool(row.skipped),
        created_at=row.created_at,
    )


def list_reader_practice_word_items(
    db: Session,
    *,
    reader_id: int,
    max_difficulty: int,
    limit: int,
) -> list[GameSessionWordItemRecord]:
    rows = db.execute(
        select(
            vocabulary_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.definition,
            vocabulary_table.c.example_sentence,
            vocabulary_table.c.difficulty_level,
            literal(reader_id).label("reader_id"),
            vocabulary_table.c.story_id,
            literal("story").label("source_type"),
            stories_generated_table.c.trait_focus,
        )
        .select_from(
            reader_vocabulary_progress_table.join(
                vocabulary_table,
                reader_vocabulary_progress_table.c.word_id == vocabulary_table.c.word_id,
            ).outerjoin(
                stories_generated_table,
                and_(
                    vocabulary_table.c.story_id == stories_generated_table.c.story_id,
                    stories_generated_table.c.reader_id == reader_id,
                ),
            )
        )
        .where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                vocabulary_table.c.difficulty_level <= max_difficulty,
                vocabulary_table.c.word.is_not(None),
            )
        )
        .order_by(
            reader_vocabulary_progress_table.c.mastery_level.asc(),
            desc(reader_vocabulary_progress_table.c.last_seen),
            vocabulary_table.c.word.asc(),
        )
        .limit(limit)
    ).mappings().all()
    return [_to_word_item(row) for row in rows if _to_word_item(row) is not None]


def list_reader_story_word_items(
    db: Session,
    *,
    reader_id: int,
    max_difficulty: int,
    limit: int,
    story_id: int | None = None,
) -> list[GameSessionWordItemRecord]:
    conditions = [
        stories_generated_table.c.reader_id == reader_id,
        vocabulary_table.c.difficulty_level <= max_difficulty,
        vocabulary_table.c.word.is_not(None),
    ]
    if story_id is not None:
        conditions.append(vocabulary_table.c.story_id == story_id)

    rows = db.execute(
        select(
            vocabulary_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.definition,
            vocabulary_table.c.example_sentence,
            vocabulary_table.c.difficulty_level,
            literal(reader_id).label("reader_id"),
            vocabulary_table.c.story_id,
            literal("story").label("source_type"),
            stories_generated_table.c.trait_focus,
        )
        .select_from(
            vocabulary_table.join(
                stories_generated_table,
                vocabulary_table.c.story_id == stories_generated_table.c.story_id,
            )
        )
        .where(and_(*conditions))
        .order_by(desc(stories_generated_table.c.created_at), vocabulary_table.c.word.asc())
        .limit(limit)
    ).mappings().all()
    return [_to_word_item(row) for row in rows if _to_word_item(row) is not None]


def list_global_word_items(
    db: Session,
    *,
    reader_id: int,
    max_difficulty: int,
    limit: int,
    exclude_word_ids: list[int],
) -> list[GameSessionWordItemRecord]:
    conditions = [
        vocabulary_table.c.story_id.is_(None),
        vocabulary_table.c.word.is_not(None),
        or_(vocabulary_table.c.difficulty_level.is_(None), vocabulary_table.c.difficulty_level <= max_difficulty),
    ]
    if exclude_word_ids:
        conditions.append(vocabulary_table.c.word_id.notin_(exclude_word_ids))

    rows = db.execute(
        select(
            vocabulary_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.definition,
            vocabulary_table.c.example_sentence,
            vocabulary_table.c.difficulty_level,
            literal(reader_id).label("reader_id"),
            vocabulary_table.c.story_id,
            literal("global_vocab").label("source_type"),
            literal(None).label("trait_focus"),
        )
        .where(and_(*conditions))
        .order_by(vocabulary_table.c.word.asc())
        .limit(limit)
    ).mappings().all()
    return [_to_word_item(row) for row in rows if _to_word_item(row) is not None]


def create_game_session(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    game_type: str,
    source_type: str,
    source_story_id: int | None,
    difficulty_level: int,
    item_count: int,
    session_payload: dict | None,
) -> int:
    result = db.execute(
        game_sessions_table.insert().values(
            account_id=account_id,
            reader_id=reader_id,
            game_type=game_type,
            source_type=source_type,
            source_story_id=source_story_id,
            difficulty_level=difficulty_level,
            status="ready",
            item_count=item_count,
            words_attempted=0,
            words_correct=0,
            words_incorrect=0,
            hints_used=0,
            completion_status="in_progress",
            session_payload=session_payload,
        )
    )
    return int(result.inserted_primary_key[0])


def get_game_session_for_account(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    session_id: int,
) -> GameSessionRecord | None:
    row = db.execute(
        select(game_sessions_table).where(
            and_(
                game_sessions_table.c.session_id == session_id,
                game_sessions_table.c.account_id == account_id,
                game_sessions_table.c.reader_id == reader_id,
            )
        )
    ).mappings().first()
    return _to_session(row)


def list_recent_game_sessions_for_reader(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    limit: int,
) -> list[GameSessionRecord]:
    rows = db.execute(
        select(game_sessions_table)
        .where(
            and_(
                game_sessions_table.c.account_id == account_id,
                game_sessions_table.c.reader_id == reader_id,
            )
        )
        .order_by(desc(game_sessions_table.c.started_at), desc(game_sessions_table.c.session_id))
        .limit(limit)
    ).mappings().all()
    return [_to_session(row) for row in rows if _to_session(row) is not None]


def list_game_sessions_for_account(
    db: Session,
    *,
    account_id: int,
    reader_id: int | None = None,
    completion_status: str | None = None,
) -> list[GameSessionRecord]:
    conditions = [game_sessions_table.c.account_id == account_id]
    if reader_id is not None:
        conditions.append(game_sessions_table.c.reader_id == reader_id)
    if completion_status is not None:
        conditions.append(game_sessions_table.c.completion_status == completion_status)

    rows = db.execute(
        select(game_sessions_table)
        .where(and_(*conditions))
        .order_by(desc(game_sessions_table.c.started_at), desc(game_sessions_table.c.session_id))
    ).mappings().all()
    return [_to_session(row) for row in rows if _to_session(row) is not None]


def replace_word_attempts(
    db: Session,
    *,
    session_id: int,
    game_type: str,
    attempts: list[dict[str, object]],
) -> None:
    db.execute(game_word_attempts_table.delete().where(game_word_attempts_table.c.session_id == session_id))
    if not attempts:
        return

    values = [
        {
            "session_id": session_id,
            "word_id": attempt.get("word_id"),
            "word_text": attempt["word_text"],
            "game_type": game_type,
            "attempt_count": attempt["attempt_count"],
            "correct": attempt["correct"],
            "time_spent_seconds": attempt["time_spent_seconds"],
            "hint_used": attempt["hint_used"],
            "skipped": attempt["skipped"],
        }
        for attempt in attempts
    ]
    db.execute(game_word_attempts_table.insert(), values)


def list_word_attempts_for_session(db: Session, *, session_id: int) -> list[GameWordAttemptRecord]:
    rows = db.execute(
        select(game_word_attempts_table)
        .where(game_word_attempts_table.c.session_id == session_id)
        .order_by(game_word_attempts_table.c.attempt_id.asc())
    ).mappings().all()
    return [_to_word_attempt(row) for row in rows if _to_word_attempt(row) is not None]


def list_word_attempts_for_sessions(db: Session, *, session_ids: list[int]) -> list[GameWordAttemptRecord]:
    if not session_ids:
        return []

    rows = db.execute(
        select(game_word_attempts_table)
        .where(game_word_attempts_table.c.session_id.in_(session_ids))
        .order_by(game_word_attempts_table.c.session_id.asc(), game_word_attempts_table.c.attempt_id.asc())
    ).mappings().all()
    return [_to_word_attempt(row) for row in rows if _to_word_attempt(row) is not None]


def update_game_session_completion(
    db: Session,
    *,
    session_id: int,
    words_attempted: int,
    words_correct: int,
    words_incorrect: int,
    hints_used: int,
    completion_status: str,
    duration_seconds: int,
) -> None:
    db.execute(
        game_sessions_table.update()
        .where(game_sessions_table.c.session_id == session_id)
        .values(
            status="completed",
            words_attempted=words_attempted,
            words_correct=words_correct,
            words_incorrect=words_incorrect,
            hints_used=hints_used,
            completion_status=completion_status,
            duration_seconds=duration_seconds,
            ended_at=func.now(),
        )
    )
