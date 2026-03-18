from dataclasses import dataclass
import json

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, func, or_, select
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

world_rules_table = Table(
    "world_rules",
    metadata,
    Column("rule_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("rule_type", String(100)),
    Column("rule_description", Text),
    Column("created_at", TIMESTAMP),
)


@dataclass
class StoryEventRecord:
    event_id: int
    story_id: int | None
    characters: list[int] | None
    location_id: int | None
    event_summary: str | None


@dataclass
class CharacterRecord:
    character_id: int
    world_id: int | None
    name: str | None
    species: str | None
    personality_traits: list[str]
    home_location: int | None


@dataclass
class CharacterRelationshipRecord:
    relationship_id: int
    character_a: int | None
    character_b: int | None
    relationship_type: str | None
    relationship_strength: int | None


@dataclass
class WorldRuleRecord:
    rule_id: int
    world_id: int
    rule_type: str | None
    rule_description: str | None


def _normalize_character_list(value: object) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, int)]


def _normalize_traits(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _to_story_event(row) -> StoryEventRecord | None:
    if row is None:
        return None
    return StoryEventRecord(
        event_id=row.event_id,
        story_id=row.story_id,
        characters=_normalize_character_list(row.characters),
        location_id=row.location_id,
        event_summary=row.event_summary,
    )


def _to_character(row) -> CharacterRecord | None:
    if row is None:
        return None
    return CharacterRecord(
        character_id=row.character_id,
        world_id=row.world_id,
        name=row.name,
        species=row.species,
        personality_traits=_normalize_traits(row.personality_traits),
        home_location=row.home_location,
    )


def _to_relationship(row) -> CharacterRelationshipRecord | None:
    if row is None:
        return None
    return CharacterRelationshipRecord(
        relationship_id=row.relationship_id,
        character_a=row.character_a,
        character_b=row.character_b,
        relationship_type=row.relationship_type,
        relationship_strength=row.relationship_strength,
    )


def _to_world_rule(row) -> WorldRuleRecord | None:
    if row is None:
        return None
    return WorldRuleRecord(
        rule_id=row.rule_id,
        world_id=row.world_id,
        rule_type=row.rule_type,
        rule_description=row.rule_description,
    )


def world_exists(db: Session, world_id: int) -> bool:
    row = db.execute(
        select(worlds_table.c.world_id).where(worlds_table.c.world_id == world_id)
    ).first()
    return row is not None


def get_character(db: Session, character_id: int) -> CharacterRecord | None:
    row = db.execute(
        select(characters_table).where(characters_table.c.character_id == character_id)
    ).mappings().first()
    return _to_character(row)


def list_story_events_for_story(db: Session, story_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table)
        .where(story_events_table.c.story_id == story_id)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    return [record for row in rows if (record := _to_story_event(row)) is not None]


def list_story_events_for_world(db: Session, world_id: int) -> list[StoryEventRecord]:
    return list_story_events_for_worlds(db, [world_id])


def list_story_events_for_worlds(db: Session, world_ids: list[int]) -> list[StoryEventRecord]:
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
    return [record for row in rows if (record := _to_story_event(row)) is not None]


def list_story_events_for_character(db: Session, character_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table)
        .where(func.json_contains(story_events_table.c.characters, json.dumps(character_id), "$") == 1)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    return [record for row in rows if (record := _to_story_event(row)) is not None]


def list_character_relationships_for_character(
    db: Session,
    character_id: int,
) -> list[CharacterRelationshipRecord]:
    rows = db.execute(
        select(character_relationships_table)
        .where(
            or_(
                character_relationships_table.c.character_a == character_id,
                character_relationships_table.c.character_b == character_id,
            )
        )
        .order_by(character_relationships_table.c.relationship_id.asc())
    ).mappings().all()
    return [record for row in rows if (record := _to_relationship(row)) is not None]


def list_world_rules_for_world(db: Session, world_id: int) -> list[WorldRuleRecord]:
    rows = db.execute(
        select(world_rules_table)
        .where(world_rules_table.c.world_id == world_id)
        .order_by(world_rules_table.c.rule_id.asc())
    ).mappings().all()
    return [record for row in rows if (record := _to_world_rule(row)) is not None]


def list_world_location_names(db: Session, world_id: int) -> list[str]:
    rows = db.execute(
        select(locations_table.c.name)
        .where(locations_table.c.world_id == world_id)
        .order_by(locations_table.c.location_id.asc())
    ).all()
    return [row.name for row in rows if isinstance(row.name, str) and row.name.strip()]
