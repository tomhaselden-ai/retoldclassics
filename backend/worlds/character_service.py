from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


metadata = MetaData()

characters_table = Table(
    "characters",
    metadata,
    Column("character_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("species", String(100)),
    Column("personality_traits", Text),
    Column("home_location", Integer),
    Column("updated_at", TIMESTAMP),
)

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
)

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
    Column("updated_at", TIMESTAMP),
)


@dataclass
class CharacterRecord:
    character_id: int
    world_id: int | None
    name: str | None
    species: str | None
    personality_traits: Any
    home_location: int | None
    updated_at: datetime | None


def _to_character(row) -> CharacterRecord | None:
    if row is None:
        return None
    return CharacterRecord(
        character_id=row.character_id,
        world_id=row.world_id,
        name=row.name,
        species=row.species,
        personality_traits=row.personality_traits,
        home_location=row.home_location,
        updated_at=row.updated_at,
    )


def _ensure_world_exists(db: Session, world_id: int) -> None:
    row = db.execute(
        select(worlds_table.c.world_id).where(worlds_table.c.world_id == world_id)
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )


def _validate_home_location(db: Session, world_id: int, home_location: int | None) -> None:
    if home_location is None:
        return

    row = db.execute(
        select(locations_table.c.location_id)
        .where(locations_table.c.location_id == home_location)
        .where(locations_table.c.world_id == world_id)
    ).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="home_location does not belong to this world",
        )


def list_characters(db: Session, world_id: int) -> list[CharacterRecord]:
    _ensure_world_exists(db, world_id)

    rows = db.execute(
        select(characters_table)
        .where(characters_table.c.world_id == world_id)
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()

    return [_to_character(row) for row in rows]


def create_character(
    db: Session,
    world_id: int,
    name: str,
    species: str,
    personality_traits: Any,
    home_location: int | None,
) -> CharacterRecord:
    _ensure_world_exists(db, world_id)
    _validate_home_location(db, world_id, home_location)

    try:
        result = db.execute(
            characters_table.insert().values(
                world_id=world_id,
                name=name,
                species=species,
                personality_traits=personality_traits,
                home_location=home_location,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create character",
        ) from exc

    character_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(characters_table).where(characters_table.c.character_id == character_id)
    ).mappings().first()

    character = _to_character(row)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created character",
        )
    return character
