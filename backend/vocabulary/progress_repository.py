from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, TIMESTAMP, and_, desc, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session

from backend.vocabulary.vocabulary_repository import vocabulary_table


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

reader_vocabulary_progress_table = Table(
    "reader_vocabulary_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("word_id", Integer, primary_key=True),
    Column("mastery_level", Integer),
    Column("last_seen", TIMESTAMP),
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
class ReaderVocabularyProgressRecord:
    reader_id: int
    word_id: int
    mastery_level: int | None
    last_seen: datetime | None


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


def _to_progress(row) -> ReaderVocabularyProgressRecord | None:
    if row is None:
        return None
    return ReaderVocabularyProgressRecord(
        reader_id=row.reader_id,
        word_id=row.word_id,
        mastery_level=row.mastery_level,
        last_seen=row.last_seen,
    )


def get_reader_for_account(db: Session, reader_id: int, account_id: int) -> ReaderRecord:
    row = db.execute(
        select(readers_table).where(
            and_(
                readers_table.c.reader_id == reader_id,
                readers_table.c.account_id == account_id,
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


def ensure_reader_vocabulary_progress(
    db: Session,
    reader_id: int,
    word_ids: list[int],
) -> None:
    if not word_ids:
        return

    existing_rows = db.execute(
        select(reader_vocabulary_progress_table.c.word_id).where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                reader_vocabulary_progress_table.c.word_id.in_(word_ids),
            )
        )
    ).all()
    existing_word_ids = {row.word_id for row in existing_rows}

    for word_id in word_ids:
        if word_id in existing_word_ids:
            db.execute(
                reader_vocabulary_progress_table.update()
                .where(
                    and_(
                        reader_vocabulary_progress_table.c.reader_id == reader_id,
                        reader_vocabulary_progress_table.c.word_id == word_id,
                    )
                )
                .values(last_seen=datetime.utcnow())
            )
            continue

        db.execute(
            reader_vocabulary_progress_table.insert().values(
                reader_id=reader_id,
                word_id=word_id,
                mastery_level=0,
                last_seen=datetime.utcnow(),
            )
        )


def list_reader_vocabulary(db: Session, reader_id: int) -> list[dict]:
    rows = db.execute(
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
        .order_by(reader_vocabulary_progress_table.c.last_seen.desc(), vocabulary_table.c.word.asc())
    ).mappings().all()
    return [dict(row) for row in rows]


def update_reader_word_progress(
    db: Session,
    reader_id: int,
    word_id: int,
    mastery_level: int,
) -> ReaderVocabularyProgressRecord:
    if mastery_level < 0 or mastery_level > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mastery_level",
        )

    progress = _to_progress(
        db.execute(
            select(reader_vocabulary_progress_table).where(
                and_(
                    reader_vocabulary_progress_table.c.reader_id == reader_id,
                    reader_vocabulary_progress_table.c.word_id == word_id,
                )
            )
        ).mappings().first()
    )
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found for reader",
        )

    db.execute(
        reader_vocabulary_progress_table.update()
        .where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                reader_vocabulary_progress_table.c.word_id == word_id,
            )
        )
        .values(
            mastery_level=mastery_level,
            last_seen=datetime.utcnow(),
        )
    )

    row = db.execute(
        select(reader_vocabulary_progress_table).where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                reader_vocabulary_progress_table.c.word_id == word_id,
            )
        )
    ).mappings().first()
    refreshed = _to_progress(row)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reader vocabulary progress",
        )
    return refreshed


def get_practice_vocabulary(db: Session, reader_id: int, limit: int = 10) -> list[dict]:
    rows = db.execute(
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
            reader_vocabulary_progress_table.c.mastery_level.asc(),
            desc(reader_vocabulary_progress_table.c.last_seen),
            vocabulary_table.c.word.asc(),
        )
        .limit(limit)
    ).mappings().all()
    return [dict(row) for row in rows]


def sync_reader_progress_metrics(db: Session, reader_id: int) -> None:
    mastered_count = db.execute(
        select(reader_vocabulary_progress_table.c.word_id).where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                reader_vocabulary_progress_table.c.mastery_level == 3,
            )
        )
    ).all()

    existing = db.execute(
        select(reader_progress_table).where(reader_progress_table.c.reader_id == reader_id)
    ).mappings().first()

    values = {"words_mastered": len(mastered_count)}
    if existing is None:
        db.execute(
            reader_progress_table.insert().values(
                reader_id=reader_id,
                stories_read=0,
                words_mastered=len(mastered_count),
                reading_speed=None,
                preferred_themes=None,
                traits_reinforced=None,
            )
        )
        return

    db.execute(
        reader_progress_table.update()
        .where(reader_progress_table.c.reader_id == reader_id)
        .values(**values)
    )
