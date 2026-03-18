from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.readers.reader_learning_model import readers_table
from backend.worlds.reader_world_context import (
    ensure_reader_world_has_derived_world,
    get_reader_world_assignment,
    load_reader_world_context,
)


metadata = MetaData()

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Boolean),
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
    Column("personality_traits", String),
    Column("home_location", Integer),
    Column("updated_at", TIMESTAMP),
)

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


@dataclass
class WorldRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None
    updated_at: datetime | None


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
    personality_traits: object
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


@dataclass
class ReaderWorldRecord:
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
    derived_world_id: int | None
    custom_name: str | None
    created_at: datetime | None
    world: WorldRecord


def _to_world(row) -> WorldRecord | None:
    if row is None:
        return None
    return WorldRecord(
        world_id=row.world_id,
        name=row.name,
        description=row.description,
        default_world=row.default_world,
        updated_at=row.updated_at,
    )


def _to_world_rule(row) -> WorldRuleRecord | None:
    if row is None:
        return None
    return WorldRuleRecord(
        rule_id=row.rule_id,
        world_id=row.world_id,
        rule_type=row.rule_type,
        rule_description=row.rule_description,
        created_at=row.created_at,
    )


def _to_location(row) -> LocationRecord | None:
    if row is None:
        return None
    return LocationRecord(
        location_id=row.location_id,
        world_id=row.world_id,
        name=row.name,
        description=row.description,
    )


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


def _reader_belongs_to_account(db: Session, account_id: int, reader_id: int) -> bool:
    row = db.execute(
        select(readers_table.c.reader_id)
        .where(readers_table.c.reader_id == reader_id)
        .where(readers_table.c.account_id == account_id)
    ).first()
    return row is not None


def get_world(db: Session, world_id: int) -> WorldRecord:
    row = db.execute(
        select(worlds_table).where(worlds_table.c.world_id == world_id)
    ).mappings().first()
    world = _to_world(row)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return world


def list_worlds(db: Session) -> list[WorldRecord]:
    rows = db.execute(
        select(
            worlds_table.c.world_id,
            worlds_table.c.name,
            worlds_table.c.description,
            worlds_table.c.default_world,
            worlds_table.c.updated_at,
        ).order_by(worlds_table.c.world_id.asc())
    ).mappings().all()
    return [_to_world(row) for row in rows]


def get_world_details(db: Session, world_id: int) -> dict:
    world = get_world(db, world_id)

    location_rows = db.execute(
        select(locations_table)
        .where(locations_table.c.world_id == world_id)
        .order_by(locations_table.c.location_id.asc())
    ).mappings().all()

    character_rows = db.execute(
        select(characters_table)
        .where(characters_table.c.world_id == world_id)
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()

    rule_rows = db.execute(
        select(world_rules_table)
        .where(world_rules_table.c.world_id == world_id)
        .order_by(world_rules_table.c.rule_id.asc())
    ).mappings().all()

    return {
        "world": world,
        "locations": [_to_location(row) for row in location_rows],
        "characters": [_to_character(row) for row in character_rows],
        "world_rules": [_to_world_rule(row) for row in rule_rows],
    }


def get_reader_world_details(db: Session, account_id: int, reader_id: int, world_id: int) -> dict:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    reader_world, _ = get_reader_world_assignment(db, reader_id, world_id)
    context = load_reader_world_context(db, reader_world.reader_world_id)
    return {
        "world": context["world"],
        "locations": context["locations"],
        "characters": context["characters"],
        "relationships": context["relationships"],
        "world_rules": context["world_rules"],
    }


def get_reader_world_context_for_account(
    db: Session,
    account_id: int,
    reader_id: int,
    world_id: int,
) -> dict:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    reader_world, _ = get_reader_world_assignment(db, reader_id, world_id)
    return load_reader_world_context(db, reader_world.reader_world_id)


def create_reader_world_location(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    name: str,
    description: str | None,
) -> LocationRecord:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    reader_world, _ = get_reader_world_assignment(db, reader_id, template_world_id)
    derived_world_id = ensure_reader_world_has_derived_world(db, reader_world.reader_world_id)

    try:
        result = db.execute(
            locations_table.insert().values(
                world_id=derived_world_id,
                name=name,
                description=description,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create location",
        ) from exc

    location_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(locations_table).where(locations_table.c.location_id == location_id)
    ).mappings().first()
    location = _to_location(row)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created location",
        )
    return location


def create_reader_world_character(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    name: str,
    species: str,
    personality_traits: object,
    home_location: int | None,
) -> CharacterRecord:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    reader_world, _ = get_reader_world_assignment(db, reader_id, template_world_id)
    context = load_reader_world_context(db, reader_world.reader_world_id)
    derived_world_id = context["derived_world"].world_id

    if home_location is not None:
        valid_location_ids = {
            location.location_id
            for location in context["locations"]
            if isinstance(location.location_id, int)
        }
        if home_location not in valid_location_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="home_location does not belong to this reader world",
            )

    try:
        result = db.execute(
            characters_table.insert().values(
                world_id=derived_world_id,
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


def create_reader_world_relationship(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    character_a: int,
    character_b: int,
    relationship_type: str,
    relationship_strength: int,
):
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    reader_world, _ = get_reader_world_assignment(db, reader_id, template_world_id)
    context = load_reader_world_context(db, reader_world.reader_world_id)
    valid_character_ids = {
        character.character_id
        for character in context["characters"]
        if isinstance(character.character_id, int)
    }
    if character_a not in valid_character_ids or character_b not in valid_character_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Characters must belong to this reader world",
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


def assign_world_to_reader(
    db: Session,
    account_id: int,
    reader_id: int,
    world_id: int | None,
    custom_name: str | None,
) -> ReaderWorldRecord:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    if world_id is None:
        default_world_row = db.execute(
            select(worlds_table).where(worlds_table.c.default_world == True)
        ).mappings().first()
        if default_world_row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No default world available",
            )
        world = _to_world(default_world_row)
    else:
        world = get_world(db, world_id)

    try:
        result = db.execute(
            reader_worlds_table.insert().values(
                reader_id=reader_id,
                world_id=world.world_id,
                custom_name=custom_name,
            )
        )
        reader_world_id = int(result.inserted_primary_key[0])
        ensure_reader_world_has_derived_world(db, reader_world_id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign world",
        ) from exc

    row = db.execute(
        select(reader_worlds_table)
        .where(reader_worlds_table.c.reader_world_id == reader_world_id)
    ).mappings().first()

    return ReaderWorldRecord(
        reader_world_id=row.reader_world_id,
        reader_id=row.reader_id,
        world_id=row.world_id,
        derived_world_id=getattr(row, "derived_world_id", None),
        custom_name=row.custom_name,
        created_at=row.created_at,
        world=world,
    )


def list_reader_worlds(db: Session, account_id: int, reader_id: int) -> list[ReaderWorldRecord]:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    rows = db.execute(
        select(
            reader_worlds_table.c.reader_world_id,
            reader_worlds_table.c.reader_id,
            reader_worlds_table.c.world_id,
            reader_worlds_table.c.custom_name,
            reader_worlds_table.c.created_at,
            worlds_table.c.name.label("world_name"),
            worlds_table.c.description.label("world_description"),
            worlds_table.c.default_world.label("world_default_world"),
            worlds_table.c.updated_at.label("world_updated_at"),
        )
        .select_from(
            reader_worlds_table.join(
                worlds_table, reader_worlds_table.c.world_id == worlds_table.c.world_id
            )
        )
        .where(reader_worlds_table.c.reader_id == reader_id)
        .order_by(reader_worlds_table.c.reader_world_id.asc())
    ).mappings().all()

    return [
        ReaderWorldRecord(
            reader_world_id=row.reader_world_id,
            reader_id=row.reader_id,
            world_id=row.world_id,
            derived_world_id=getattr(row, "derived_world_id", None),
            custom_name=row.custom_name,
            created_at=row.created_at,
            world=WorldRecord(
                world_id=row.world_id,
                name=row.world_name,
                description=row.world_description,
                default_world=row.world_default_world,
                updated_at=row.world_updated_at,
            ),
        )
        for row in rows
    ]
