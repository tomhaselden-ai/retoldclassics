from dataclasses import dataclass
from datetime import datetime
import json

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, func, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

story_events_table = Table(
    "story_events",
    metadata,
    Column("event_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("characters", JSON),
    Column("location_id", Integer),
    Column("event_summary", Text),
)

story_versions_table = Table(
    "story_versions",
    metadata,
    Column("story_version_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("version_number", Integer),
    Column("title", String(255)),
    Column("trait_focus", String(100)),
    Column("version_notes", Text),
    Column("created_at", TIMESTAMP),
)

scene_versions_table = Table(
    "scene_versions",
    metadata,
    Column("scene_version_id", Integer, primary_key=True),
    Column("scene_id", Integer),
    Column("version_number", Integer),
    Column("scene_text", Text),
    Column("illustration_url", Text),
    Column("audio_url", Text),
    Column("created_at", TIMESTAMP),
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

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
    Column("updated_at", TIMESTAMP),
)

readers_table = Table(
    "readers",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("account_id", Integer),
)

stories_generated_table = Table(
    "stories_generated",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("reader_id", Integer),
)


@dataclass
class StoryEventRecord:
    event_id: int
    story_id: int | None
    characters: list[int] | None
    location_id: int | None
    event_summary: str | None


@dataclass
class StoryVersionRecord:
    story_version_id: int
    story_id: int
    version_number: int
    title: str | None
    trait_focus: str | None
    version_notes: str | None
    created_at: datetime | None


@dataclass
class SceneVersionRecord:
    scene_version_id: int
    scene_id: int
    version_number: int
    scene_text: str | None
    illustration_url: str | None
    audio_url: str | None
    created_at: datetime | None


def _normalize_characters(value: object) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None
    normalized: list[int] = []
    for item in value:
        if isinstance(item, int):
            normalized.append(item)
    return normalized


def _to_story_event(row) -> StoryEventRecord | None:
    if row is None:
        return None
    return StoryEventRecord(
        event_id=row.event_id,
        story_id=row.story_id,
        characters=_normalize_characters(row.characters),
        location_id=row.location_id,
        event_summary=row.event_summary,
    )


def _to_story_version(row) -> StoryVersionRecord | None:
    if row is None:
        return None
    return StoryVersionRecord(
        story_version_id=row.story_version_id,
        story_id=row.story_id,
        version_number=row.version_number,
        title=row.title,
        trait_focus=row.trait_focus,
        version_notes=row.version_notes,
        created_at=row.created_at,
    )


def _to_scene_version(row) -> SceneVersionRecord | None:
    if row is None:
        return None
    return SceneVersionRecord(
        scene_version_id=row.scene_version_id,
        scene_id=row.scene_id,
        version_number=row.version_number,
        scene_text=row.scene_text,
        illustration_url=row.illustration_url,
        audio_url=row.audio_url,
        created_at=row.created_at,
    )


def list_story_events_by_story(db: Session, story_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table)
        .where(story_events_table.c.story_id == story_id)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    records: list[StoryEventRecord] = []
    for row in rows:
        record = _to_story_event(row)
        if record is not None:
            records.append(record)
    return records


def list_story_events_by_character(db: Session, character_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table)
        .where(func.json_contains(story_events_table.c.characters, json.dumps(character_id), "$") == 1)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    records: list[StoryEventRecord] = []
    for row in rows:
        record = _to_story_event(row)
        if record is not None:
            records.append(record)
    return records


def list_story_events_by_world(db: Session, world_id: int) -> list[StoryEventRecord]:
    return list_story_events_by_worlds(db, [world_id])


def list_story_events_by_worlds(db: Session, world_ids: list[int]) -> list[StoryEventRecord]:
    if not world_ids:
        return []
    rows = db.execute(
        select(story_events_table)
        .select_from(
            story_events_table.join(
                locations_table,
                story_events_table.c.location_id == locations_table.c.location_id,
            )
        )
        .where(locations_table.c.world_id.in_(world_ids))
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    records: list[StoryEventRecord] = []
    for row in rows:
        record = _to_story_event(row)
        if record is not None:
            records.append(record)
    return records


def character_exists(db: Session, character_id: int) -> bool:
    row = db.execute(
        select(characters_table.c.character_id).where(characters_table.c.character_id == character_id)
    ).first()
    return row is not None


def location_exists(db: Session, location_id: int) -> bool:
    row = db.execute(
        select(locations_table.c.location_id).where(locations_table.c.location_id == location_id)
    ).first()
    return row is not None


def world_exists(db: Session, world_id: int) -> bool:
    row = db.execute(
        select(worlds_table.c.world_id).where(worlds_table.c.world_id == world_id)
    ).first()
    return row is not None


def story_belongs_to_account(db: Session, story_id: int, account_id: int) -> bool:
    row = db.execute(
        select(stories_generated_table.c.story_id)
        .select_from(
            stories_generated_table.join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(stories_generated_table.c.story_id == story_id)
        .where(readers_table.c.account_id == account_id)
    ).first()
    return row is not None


def list_existing_character_ids(db: Session, character_ids: list[int]) -> set[int]:
    if not character_ids:
        return set()

    rows = db.execute(
        select(characters_table.c.character_id).where(characters_table.c.character_id.in_(character_ids))
    ).all()
    return {int(row.character_id) for row in rows}


def insert_story_event(
    db: Session,
    story_id: int,
    characters: list[int] | None,
    location_id: int | None,
    event_summary: str,
) -> StoryEventRecord:
    result = db.execute(
        story_events_table.insert().values(
            story_id=story_id,
            characters=characters,
            location_id=location_id,
            event_summary=event_summary,
        )
    )
    event_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(story_events_table).where(story_events_table.c.event_id == event_id)
    ).mappings().first()
    event = _to_story_event(row)
    if event is None:
        raise RuntimeError("Inserted story event could not be reloaded")
    return event


def get_next_story_version_number(db: Session, story_id: int) -> int:
    row = db.execute(
        select(func.max(story_versions_table.c.version_number).label("max_version"))
        .where(story_versions_table.c.story_id == story_id)
    ).mappings().first()
    if row is None or row.max_version is None:
        return 1
    return int(row.max_version) + 1


def insert_story_version(
    db: Session,
    story_id: int,
    version_number: int,
    title: str | None,
    trait_focus: str | None,
    version_notes: str | None,
) -> StoryVersionRecord:
    result = db.execute(
        story_versions_table.insert().values(
            story_id=story_id,
            version_number=version_number,
            title=title,
            trait_focus=trait_focus,
            version_notes=version_notes,
        )
    )
    story_version_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(story_versions_table).where(story_versions_table.c.story_version_id == story_version_id)
    ).mappings().first()
    version = _to_story_version(row)
    if version is None:
        raise RuntimeError("Inserted story version could not be reloaded")
    return version


def get_next_scene_version_number(db: Session, scene_id: int) -> int:
    row = db.execute(
        select(func.max(scene_versions_table.c.version_number).label("max_version"))
        .where(scene_versions_table.c.scene_id == scene_id)
    ).mappings().first()
    if row is None or row.max_version is None:
        return 1
    return int(row.max_version) + 1


def insert_scene_version(
    db: Session,
    scene_id: int,
    version_number: int,
    scene_text: str | None,
    illustration_url: str | None,
    audio_url: str | None,
) -> SceneVersionRecord:
    result = db.execute(
        scene_versions_table.insert().values(
            scene_id=scene_id,
            version_number=version_number,
            scene_text=scene_text,
            illustration_url=illustration_url,
            audio_url=audio_url,
        )
    )
    scene_version_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(scene_versions_table).where(scene_versions_table.c.scene_version_id == scene_version_id)
    ).mappings().first()
    version = _to_scene_version(row)
    if version is None:
        raise RuntimeError("Inserted scene version could not be reloaded")
    return version
