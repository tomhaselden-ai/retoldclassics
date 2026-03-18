import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, desc, func, select
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

narration_audio_table = Table(
    "narration_audio",
    metadata,
    Column("audio_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("scene_id", Integer),
    Column("audio_url", Text),
    Column("speech_marks_json", JSON),
    Column("voice", String(50)),
    Column("generated_at", TIMESTAMP),
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

story_events_table = Table(
    "story_events",
    metadata,
    Column("event_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("characters", JSON),
    Column("location_id", Integer),
    Column("event_summary", Text),
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
class StoryRecord:
    story_id: int
    reader_id: int | None
    reader_world_id: int | None
    title: str | None
    trait_focus: str | None
    current_version: int | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class SceneRecord:
    scene_id: int
    story_id: int | None
    scene_order: int | None
    scene_text: str | None
    illustration_url: str | None
    audio_url: str | None


@dataclass
class NarrationRecord:
    audio_id: int
    story_id: int | None
    scene_id: int | None
    audio_url: str | None
    speech_marks_json: object
    voice: str | None
    generated_at: datetime | None


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
class LocationRecord:
    location_id: int
    world_id: int | None
    name: str | None
    description: str | None


@dataclass
class StoryEventRecord:
    event_id: int
    story_id: int | None
    characters: object
    location_id: int | None
    event_summary: str | None


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


def _to_story(row) -> StoryRecord | None:
    if row is None:
        return None
    return StoryRecord(
        story_id=row.story_id,
        reader_id=row.reader_id,
        reader_world_id=row.reader_world_id,
        title=row.title,
        trait_focus=row.trait_focus,
        current_version=row.current_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_scene(row) -> SceneRecord | None:
    if row is None:
        return None
    return SceneRecord(
        scene_id=row.scene_id,
        story_id=row.story_id,
        scene_order=row.scene_order,
        scene_text=row.scene_text,
        illustration_url=row.illustration_url,
        audio_url=row.audio_url,
    )


def _to_narration(row) -> NarrationRecord | None:
    if row is None:
        return None
    return NarrationRecord(
        audio_id=row.audio_id,
        story_id=row.story_id,
        scene_id=row.scene_id,
        audio_url=row.audio_url,
        speech_marks_json=row.speech_marks_json,
        voice=row.voice,
        generated_at=row.generated_at,
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


def _to_story_event(row) -> StoryEventRecord | None:
    if row is None:
        return None
    return StoryEventRecord(
        event_id=row.event_id,
        story_id=row.story_id,
        characters=row.characters,
        location_id=row.location_id,
        event_summary=row.event_summary,
    )


def get_reader(db: Session, reader_id: int) -> ReaderRecord | None:
    row = db.execute(
        select(readers_table).where(readers_table.c.reader_id == reader_id)
    ).mappings().first()
    return _to_reader(row)


def get_reader_world_by_id(db: Session, reader_id: int, reader_world_id: int) -> ReaderWorldRecord | None:
    row = db.execute(
        select(reader_worlds_table).where(
            and_(
                reader_worlds_table.c.reader_id == reader_id,
                reader_worlds_table.c.reader_world_id == reader_world_id,
            )
        )
    ).mappings().first()
    return _to_reader_world(row)


def get_latest_reader_world(db: Session, reader_id: int) -> ReaderWorldRecord | None:
    row = db.execute(
        select(reader_worlds_table)
        .where(reader_worlds_table.c.reader_id == reader_id)
        .order_by(desc(reader_worlds_table.c.created_at), desc(reader_worlds_table.c.reader_world_id))
        .limit(1)
    ).mappings().first()
    return _to_reader_world(row)


def get_reader_world_by_world_id(db: Session, reader_id: int, world_id: int) -> ReaderWorldRecord | None:
    row = db.execute(
        select(reader_worlds_table).where(
            and_(
                reader_worlds_table.c.reader_id == reader_id,
                reader_worlds_table.c.world_id == world_id,
            )
        )
    ).mappings().first()
    return _to_reader_world(row)


def get_world(db: Session, world_id: int) -> WorldRecord | None:
    row = db.execute(
        select(worlds_table).where(worlds_table.c.world_id == world_id)
    ).mappings().first()
    return _to_world(row)


def get_world_by_name(db: Session, world_name: str) -> WorldRecord | None:
    row = db.execute(
        select(worlds_table).where(func.lower(worlds_table.c.name) == world_name.strip().lower())
    ).mappings().first()
    return _to_world(row)


def get_story_for_reader(db: Session, reader_id: int, story_id: int) -> StoryRecord | None:
    row = db.execute(
        select(stories_generated_table).where(
            and_(
                stories_generated_table.c.reader_id == reader_id,
                stories_generated_table.c.story_id == story_id,
            )
        )
    ).mappings().first()
    return _to_story(row)


def get_latest_story_for_reader(
    db: Session,
    reader_id: int,
    reader_world_id: int | None = None,
) -> StoryRecord | None:
    query = select(stories_generated_table).where(stories_generated_table.c.reader_id == reader_id)
    if reader_world_id is not None:
        query = query.where(stories_generated_table.c.reader_world_id == reader_world_id)
    row = db.execute(
        query.order_by(
            desc(stories_generated_table.c.updated_at),
            desc(stories_generated_table.c.created_at),
            desc(stories_generated_table.c.story_id),
        ).limit(1)
    ).mappings().first()
    return _to_story(row)


def get_first_story_scene(db: Session, story_id: int) -> SceneRecord | None:
    row = db.execute(
        select(story_scenes_table)
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
        .limit(1)
    ).mappings().first()
    return _to_scene(row)


def get_story_scene_by_order(db: Session, story_id: int, scene_order: int) -> SceneRecord | None:
    row = db.execute(
        select(story_scenes_table).where(
            and_(
                story_scenes_table.c.story_id == story_id,
                story_scenes_table.c.scene_order == scene_order,
            )
        )
    ).mappings().first()
    return _to_scene(row)


def get_next_story_scene(db: Session, story_id: int, current_scene_order: int) -> SceneRecord | None:
    row = db.execute(
        select(story_scenes_table)
        .where(
            and_(
                story_scenes_table.c.story_id == story_id,
                story_scenes_table.c.scene_order > current_scene_order,
            )
        )
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
        .limit(1)
    ).mappings().first()
    return _to_scene(row)


def get_narration_for_scene(db: Session, story_id: int, scene_id: int) -> NarrationRecord | None:
    row = db.execute(
        select(narration_audio_table).where(
            and_(
                narration_audio_table.c.story_id == story_id,
                narration_audio_table.c.scene_id == scene_id,
            )
        )
    ).mappings().first()
    return _to_narration(row)


def get_character_by_name(db: Session, world_id: int, character_name: str) -> CharacterRecord | None:
    row = db.execute(
        select(characters_table).where(
            and_(
                characters_table.c.world_id == world_id,
                func.lower(characters_table.c.name) == character_name.strip().lower(),
            )
        )
    ).mappings().first()
    return _to_character(row)


def get_character_by_species(db: Session, world_id: int, species_name: str) -> CharacterRecord | None:
    row = db.execute(
        select(characters_table).where(
            and_(
                characters_table.c.world_id == world_id,
                func.lower(characters_table.c.species) == species_name.strip().lower(),
            )
        )
    ).mappings().first()
    return _to_character(row)


def get_location(db: Session, location_id: int) -> LocationRecord | None:
    row = db.execute(
        select(locations_table).where(locations_table.c.location_id == location_id)
    ).mappings().first()
    return _to_location(row)


def list_story_events_for_character(db: Session, character_id: int, limit: int = 3) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table)
        .where(func.json_contains(story_events_table.c.characters, json.dumps(character_id), "$") == 1)
        .order_by(desc(story_events_table.c.event_id))
        .limit(limit)
    ).mappings().all()
    return [_to_story_event(row) for row in rows if _to_story_event(row) is not None]
