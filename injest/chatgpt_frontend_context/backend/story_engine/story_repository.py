import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


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

reader_worlds_table = Table(
    "reader_worlds",
    metadata,
    Column("reader_world_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("world_id", Integer),
    Column("custom_name", String(255)),
    Column("created_at", TIMESTAMP),
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

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
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

stories_table = Table(
    "stories",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("source_author", String(100)),
    Column("source_story_id", Integer),
    Column("title", String(255)),
    Column("age_range", String(50)),
    Column("reading_level", String(50)),
    Column("moral", Text),
    Column("characters", JSON),
    Column("locations", JSON),
    Column("traits", JSON),
    Column("themes", JSON),
    Column("scenes", JSON),
    Column("beats", JSON),
    Column("paragraphs_modern", JSON),
    Column("narration", JSON),
    Column("illustration_prompts", JSON),
    Column("created_at", TIMESTAMP),
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

story_scenes_table = Table(
    "story_scenes",
    metadata,
    Column("scene_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("scene_order", Integer),
    Column("scene_text", Text),
    Column("illustration_url", Text),
    Column("audio_url", Text),
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


@dataclass
class ReaderWorldRecord:
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
    custom_name: str | None
    created_at: datetime | None


@dataclass
class WorldRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: int | None
    updated_at: datetime | None


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
class LocationRecord:
    location_id: int
    world_id: int | None
    name: str | None
    description: str | None


@dataclass
class RelationshipRecord:
    relationship_id: int
    character_a: int | None
    character_b: int | None
    relationship_type: str | None
    relationship_strength: int | None
    last_interaction: datetime | None


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


def _to_reader_world(row) -> ReaderWorldRecord | None:
    if row is None:
        return None
    return ReaderWorldRecord(
        reader_world_id=row.reader_world_id,
        reader_id=row.reader_id,
        world_id=row.world_id,
        custom_name=row.custom_name,
        created_at=row.created_at,
    )


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


def _to_location(row) -> LocationRecord | None:
    if row is None:
        return None
    return LocationRecord(
        location_id=row.location_id,
        world_id=row.world_id,
        name=row.name,
        description=row.description,
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


def load_reader(db: Session, reader_id: int) -> ReaderRecord:
    row = db.execute(
        select(readers_table).where(readers_table.c.reader_id == reader_id)
    ).mappings().first()
    reader = _to_reader(row)
    if reader is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found",
        )
    return reader


def load_reader_world(db: Session, reader_id: int, world_id: int) -> tuple[ReaderWorldRecord, WorldRecord]:
    row = db.execute(
        select(reader_worlds_table, worlds_table)
        .select_from(
            reader_worlds_table.join(
                worlds_table,
                reader_worlds_table.c.world_id == worlds_table.c.world_id,
            )
        )
        .where(
            and_(
                reader_worlds_table.c.reader_id == reader_id,
                reader_worlds_table.c.world_id == world_id,
            )
        )
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader has no assigned world for the requested world_id",
        )

    reader_world = _to_reader_world(row)
    world = _to_world(row)
    return reader_world, world


def load_world_context(db: Session, world_id: int) -> dict[str, Any]:
    world_row = db.execute(
        select(worlds_table).where(worlds_table.c.world_id == world_id)
    ).mappings().first()
    world = _to_world(world_row)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )

    character_rows = db.execute(
        select(characters_table)
        .where(characters_table.c.world_id == world_id)
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()
    location_rows = db.execute(
        select(locations_table)
        .where(locations_table.c.world_id == world_id)
        .order_by(locations_table.c.location_id.asc())
    ).mappings().all()

    character_ids = [row.character_id for row in character_rows]
    relationship_rows = []
    if character_ids:
        relationship_rows = db.execute(
            select(character_relationships_table)
            .where(character_relationships_table.c.character_a.in_(character_ids))
            .where(character_relationships_table.c.character_b.in_(character_ids))
            .order_by(character_relationships_table.c.relationship_id.asc())
        ).mappings().all()

    return {
        "world": world,
        "characters": [_to_character(row) for row in character_rows],
        "locations": [_to_location(row) for row in location_rows],
        "relationships": [_to_relationship(row) for row in relationship_rows],
    }


def create_generated_story(
    db: Session,
    reader_id: int,
    reader_world_id: int,
    title: str,
    trait_focus: str | None,
) -> int:
    result = db.execute(
        stories_generated_table.insert().values(
            reader_id=reader_id,
            reader_world_id=reader_world_id,
            title=title,
            trait_focus=trait_focus,
            current_version=1,
        )
    )
    return int(result.inserted_primary_key[0])


def create_story_scene(
    db: Session,
    story_id: int,
    scene_order: int,
    scene_payload: dict[str, Any],
) -> None:
    db.execute(
        story_scenes_table.insert().values(
            story_id=story_id,
            scene_order=scene_order,
            scene_text=json.dumps(scene_payload, ensure_ascii=False),
            illustration_url=None,
            audio_url=None,
        )
    )
