from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.readers.reader_learning_model import readers_table


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
class ReaderWorldRecord:
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
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


def assign_world_to_reader(
    db: Session,
    account_id: int,
    reader_id: int,
    custom_name: str | None,
) -> ReaderWorldRecord:
    if not _reader_belongs_to_account(db, account_id, reader_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )

    default_world_row = db.execute(
        select(worlds_table).where(worlds_table.c.default_world == True)
    ).mappings().first()
    if default_world_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No default world available",
        )

    world = _to_world(default_world_row)

    try:
        result = db.execute(
            reader_worlds_table.insert().values(
                reader_id=reader_id,
                world_id=world.world_id,
                custom_name=custom_name,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign world",
        ) from exc

    reader_world_id = int(result.inserted_primary_key[0])

    row = db.execute(
        select(reader_worlds_table)
        .where(reader_worlds_table.c.reader_world_id == reader_world_id)
    ).mappings().first()

    return ReaderWorldRecord(
        reader_world_id=row.reader_world_id,
        reader_id=row.reader_id,
        world_id=row.world_id,
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
