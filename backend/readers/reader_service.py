from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.readers.reader_learning_model import (
    bookshelves_table,
    reader_progress_table,
    readers_table,
)


@dataclass
class ReaderRecord:
    reader_id: int
    account_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    gender_preference: str | None
    trait_focus: Any
    created_at: datetime | None


def _to_reader_record(row) -> ReaderRecord | None:
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


def _get_reader_by_id(db: Session, reader_id: int) -> ReaderRecord | None:
    row = db.execute(
        readers_table.select().where(readers_table.c.reader_id == reader_id)
    ).mappings().first()
    return _to_reader_record(row)


def _get_owned_reader(db: Session, account_id: int, reader_id: int) -> ReaderRecord:
    reader = _get_reader_by_id(db, reader_id)
    if reader is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    if reader.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reader does not belong to this account",
        )

    return reader


def create_reader(
    db: Session,
    account_id: int,
    name: str,
    age: int,
    reading_level: str,
    gender_preference: str,
    trait_focus: Any,
) -> ReaderRecord:
    try:
        result = db.execute(
            readers_table.insert().values(
                account_id=account_id,
                name=name,
                age=age,
                reading_level=reading_level,
                gender_preference=gender_preference,
                trait_focus=trait_focus,
            )
        )
        reader_id = int(result.inserted_primary_key[0])

        db.execute(
            bookshelves_table.insert().values(
                reader_id=reader_id,
            )
        )

        db.execute(
            reader_progress_table.insert().values(
                reader_id=reader_id,
                stories_read=0,
                words_mastered=0,
                reading_speed=None,
                preferred_themes=None,
                traits_reinforced=None,
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reader",
        ) from exc

    reader = _get_reader_by_id(db, reader_id)
    if reader is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created reader",
        )
    return reader


def list_readers(db: Session, account_id: int) -> list[ReaderRecord]:
    rows = db.execute(
        readers_table.select()
        .where(readers_table.c.account_id == account_id)
        .order_by(readers_table.c.reader_id.asc())
    ).mappings().all()
    return [_to_reader_record(row) for row in rows]


def get_reader(db: Session, account_id: int, reader_id: int) -> ReaderRecord:
    return _get_owned_reader(db, account_id, reader_id)


def update_reader(
    db: Session,
    account_id: int,
    reader_id: int,
    name: str,
    age: int,
    reading_level: str,
    gender_preference: str,
    trait_focus: Any,
) -> ReaderRecord:
    _get_owned_reader(db, account_id, reader_id)

    try:
        db.execute(
            readers_table.update()
            .where(readers_table.c.reader_id == reader_id)
            .values(
                name=name,
                age=age,
                reading_level=reading_level,
                gender_preference=gender_preference,
                trait_focus=trait_focus,
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reader",
        ) from exc

    return _get_owned_reader(db, account_id, reader_id)


def delete_reader(db: Session, account_id: int, reader_id: int) -> None:
    _get_owned_reader(db, account_id, reader_id)

    try:
        db.execute(
            readers_table.delete().where(readers_table.c.reader_id == reader_id)
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reader",
        ) from exc
