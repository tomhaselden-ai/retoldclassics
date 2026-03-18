from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import Column, Float, Integer, MetaData, Table, TIMESTAMP, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

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
class ReaderProgressRecord:
    reader_id: int
    stories_read: int | None
    words_mastered: int | None
    reading_speed: float | None
    preferred_themes: object
    traits_reinforced: object


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
