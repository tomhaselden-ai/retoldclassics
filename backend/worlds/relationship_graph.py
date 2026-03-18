from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


metadata = MetaData()

character_relationships_table = Table(
    "character_relationships",
    metadata,
    Column("relationship_id", Integer, primary_key=True),
    Column("character_a", Integer),
    Column("character_b", Integer),
    Column("relationship_type", String(100)),
    Column("relationship_strength", Integer),
    Column("last_interaction", TIMESTAMP),
)

characters_table = Table(
    "characters",
    metadata,
    Column("character_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("species", String(100)),
    Column("personality_traits", String),
    Column("home_location", Integer),
    Column("updated_at", TIMESTAMP),
)

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
)


@dataclass
class RelationshipRecord:
    relationship_id: int
    character_a: int | None
    character_b: int | None
    relationship_type: str | None
    relationship_strength: int | None
    last_interaction: datetime | None


def _to_relationship(row) -> RelationshipRecord | None:
    if row is None:
        return None
    return RelationshipRecord(
        relationship_id=row.relationship_id,
        character_a=row.character_a,
        character_b=row.character_b,
        relationship_type=row.relationship_type,
        relationship_strength=row.relationship_strength,
        last_interaction=row.last_interaction,
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


def _get_character_world(db: Session, character_id: int) -> int:
    row = db.execute(
        select(characters_table.c.world_id).where(characters_table.c.character_id == character_id)
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return int(row.world_id)


def list_relationships(db: Session, world_id: int) -> list[RelationshipRecord]:
    _ensure_world_exists(db, world_id)

    character_ids = db.execute(
        select(characters_table.c.character_id).where(characters_table.c.world_id == world_id)
    ).scalars().all()

    if not character_ids:
        return []

    rows = db.execute(
        select(character_relationships_table)
        .where(character_relationships_table.c.character_a.in_(character_ids))
        .where(character_relationships_table.c.character_b.in_(character_ids))
        .order_by(character_relationships_table.c.relationship_id.asc())
    ).mappings().all()

    return [_to_relationship(row) for row in rows]


def create_relationship(
    db: Session,
    character_a: int,
    character_b: int,
    relationship_type: str,
    relationship_strength: int,
) -> RelationshipRecord:
    world_a = _get_character_world(db, character_a)
    world_b = _get_character_world(db, character_b)

    if world_a != world_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Characters must belong to the same world",
        )

    try:
        result = db.execute(
            character_relationships_table.insert().values(
                character_a=character_a,
                character_b=character_b,
                relationship_type=relationship_type,
                relationship_strength=relationship_strength,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create relationship",
        ) from exc

    relationship_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(character_relationships_table).where(
            character_relationships_table.c.relationship_id == relationship_id
        )
    ).mappings().first()

    relationship = _to_relationship(row)
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created relationship",
        )
    return relationship
