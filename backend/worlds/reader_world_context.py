from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

reader_worlds_table = Table(
    "reader_worlds",
    metadata,
    Column("reader_world_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("world_id", Integer),
    Column("derived_world_id", Integer),
    Column("custom_name", String(255)),
    Column("created_at", TIMESTAMP),
)

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Boolean),
    Column("parent_world_id", Integer),
    Column("updated_at", TIMESTAMP),
)

world_rules_table = Table(
    "world_rules",
    metadata,
    Column("rule_id", Integer, primary_key=True),
    Column("world_id", Integer, nullable=False),
    Column("rule_type", String(100)),
    Column("rule_description", Text),
    Column("created_at", TIMESTAMP),
)

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
)

characters_table = Table(
    "characters",
    metadata,
    Column("character_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("species", String(100)),
    Column("personality_traits", JSON),
    Column("home_location", Integer),
    Column("updated_at", TIMESTAMP),
)

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


@dataclass
class WorldRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None
    parent_world_id: int | None
    updated_at: datetime | None


@dataclass
class ReaderWorldRecord:
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
    derived_world_id: int | None
    custom_name: str | None
    created_at: datetime | None


@dataclass
class WorldRuleRecord:
    rule_id: int
    world_id: int
    rule_type: str | None
    rule_description: str | None
    created_at: datetime | None


@dataclass
class LocationRecord:
    location_id: int
    world_id: int | None
    name: str | None
    description: str | None


@dataclass
class CharacterRecord:
    character_id: int
    world_id: int | None
    name: str | None
    species: str | None
    personality_traits: Any
    home_location: int | None
    updated_at: datetime | None


@dataclass
class RelationshipRecord:
    relationship_id: int
    character_a: int | None
    character_b: int | None
    relationship_type: str | None
    relationship_strength: int | None
    last_interaction: datetime | None


def _to_world(row: Any) -> WorldRecord | None:
    if row is None:
        return None
    return WorldRecord(
        world_id=row.world_id,
        name=row.name,
        description=row.description,
        default_world=row.default_world,
        parent_world_id=getattr(row, "parent_world_id", None),
        updated_at=row.updated_at,
    )


def _to_reader_world(row: Any) -> ReaderWorldRecord | None:
    if row is None:
        return None
    return ReaderWorldRecord(
        reader_world_id=row.reader_world_id,
        reader_id=row.reader_id,
        world_id=row.world_id,
        derived_world_id=getattr(row, "derived_world_id", None),
        custom_name=row.custom_name,
        created_at=row.created_at,
    )


def _to_world_rule(row: Any) -> WorldRuleRecord | None:
    if row is None:
        return None
    return WorldRuleRecord(
        rule_id=row.rule_id,
        world_id=row.world_id,
        rule_type=row.rule_type,
        rule_description=row.rule_description,
        created_at=row.created_at,
    )


def _to_location(row: Any) -> LocationRecord | None:
    if row is None:
        return None
    return LocationRecord(
        location_id=row.location_id,
        world_id=row.world_id,
        name=row.name,
        description=row.description,
    )


def _to_character(row: Any) -> CharacterRecord | None:
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


def _to_relationship(row: Any) -> RelationshipRecord | None:
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


def get_world_record(db: Session, world_id: int) -> WorldRecord:
    row = db.execute(select(worlds_table).where(worlds_table.c.world_id == world_id)).mappings().first()
    world = _to_world(row)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return world


def get_reader_world_record(db: Session, reader_world_id: int) -> ReaderWorldRecord:
    row = db.execute(
        select(reader_worlds_table).where(reader_worlds_table.c.reader_world_id == reader_world_id)
    ).mappings().first()
    record = _to_reader_world(row)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader world not found",
        )
    return record


def ensure_reader_world_has_derived_world(db: Session, reader_world_id: int) -> int:
    reader_world = get_reader_world_record(db, reader_world_id)
    if isinstance(reader_world.derived_world_id, int):
        derived_world = db.execute(
            select(worlds_table).where(worlds_table.c.world_id == reader_world.derived_world_id)
        ).mappings().first()
        if derived_world is not None:
            return reader_world.derived_world_id

    if not isinstance(reader_world.world_id, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader world is missing a template world",
        )

    template_world = get_world_record(db, reader_world.world_id)
    result = db.execute(
        worlds_table.insert().values(
            name=reader_world.custom_name or template_world.name,
            description=template_world.description,
            default_world=False,
            parent_world_id=template_world.world_id,
        )
    )
    derived_world_id = int(result.inserted_primary_key[0])
    db.execute(
        reader_worlds_table.update()
        .where(reader_worlds_table.c.reader_world_id == reader_world.reader_world_id)
        .values(derived_world_id=derived_world_id)
    )
    return derived_world_id


def get_reader_world_assignment(db: Session, reader_id: int, template_world_id: int) -> tuple[ReaderWorldRecord, WorldRecord]:
    row = db.execute(
        select(reader_worlds_table)
        .where(
            and_(
                reader_worlds_table.c.reader_id == reader_id,
                reader_worlds_table.c.world_id == template_world_id,
            )
        )
    ).mappings().first()
    reader_world = _to_reader_world(row)
    if reader_world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader has no assigned world for the requested world_id",
        )

    ensure_reader_world_has_derived_world(db, reader_world.reader_world_id)
    reader_world = get_reader_world_record(db, reader_world.reader_world_id)
    template_world = get_world_record(db, template_world_id)
    return reader_world, template_world


def _load_locations_for_worlds(db: Session, world_ids: list[int]) -> list[LocationRecord]:
    if not world_ids:
        return []
    rows = db.execute(
        select(locations_table)
        .where(locations_table.c.world_id.in_(world_ids))
        .order_by(locations_table.c.world_id.asc(), locations_table.c.location_id.asc())
    ).mappings().all()
    return [_to_location(row) for row in rows]


def _load_characters_for_worlds(db: Session, world_ids: list[int]) -> list[CharacterRecord]:
    if not world_ids:
        return []
    rows = db.execute(
        select(characters_table)
        .where(characters_table.c.world_id.in_(world_ids))
        .order_by(characters_table.c.world_id.asc(), characters_table.c.character_id.asc())
    ).mappings().all()
    return [_to_character(row) for row in rows]


def _load_world_rules_for_worlds(db: Session, world_ids: list[int]) -> list[WorldRuleRecord]:
    if not world_ids:
        return []
    rows = db.execute(
        select(world_rules_table)
        .where(world_rules_table.c.world_id.in_(world_ids))
        .order_by(world_rules_table.c.world_id.asc(), world_rules_table.c.rule_id.asc())
    ).mappings().all()
    return [_to_world_rule(row) for row in rows]


def load_reader_world_context(db: Session, reader_world_id: int) -> dict[str, Any]:
    reader_world = get_reader_world_record(db, reader_world_id)
    derived_world_id = ensure_reader_world_has_derived_world(db, reader_world_id)
    reader_world = get_reader_world_record(db, reader_world_id)

    if not isinstance(reader_world.world_id, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader world is missing a template world",
        )

    template_world = get_world_record(db, reader_world.world_id)
    derived_world = get_world_record(db, derived_world_id)
    world_ids = [template_world.world_id, derived_world.world_id]

    locations = _load_locations_for_worlds(db, world_ids)
    characters = _load_characters_for_worlds(db, world_ids)
    world_rules = _load_world_rules_for_worlds(db, world_ids)

    character_ids = [character.character_id for character in characters if isinstance(character.character_id, int)]
    relationships: list[RelationshipRecord] = []
    if character_ids:
        relationship_rows = db.execute(
            select(character_relationships_table)
            .where(character_relationships_table.c.character_a.in_(character_ids))
            .where(character_relationships_table.c.character_b.in_(character_ids))
            .order_by(character_relationships_table.c.relationship_id.asc())
        ).mappings().all()
        relationships = [_to_relationship(row) for row in relationship_rows]

    display_world = replace(
        derived_world,
        name=reader_world.custom_name or derived_world.name or template_world.name,
        description=derived_world.description or template_world.description,
    )

    return {
        "reader_world": reader_world,
        "world": display_world,
        "template_world": template_world,
        "derived_world": derived_world,
        "locations": locations,
        "characters": characters,
        "relationships": relationships,
        "world_rules": world_rules,
    }


def create_reader_world_character(
    db: Session,
    reader_world_id: int,
    name: str,
    species: str,
    personality_traits: list[str],
    home_location: int | None,
) -> CharacterRecord:
    derived_world_id = ensure_reader_world_has_derived_world(db, reader_world_id)
    result = db.execute(
        characters_table.insert().values(
            world_id=derived_world_id,
            name=name,
            species=species,
            personality_traits=personality_traits,
            home_location=home_location,
        )
    )
    character_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(characters_table).where(characters_table.c.character_id == character_id)
    ).mappings().first()
    character = _to_character(row)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reader world character",
        )
    return character
