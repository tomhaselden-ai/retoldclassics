import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, desc, func, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

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

illustrations_table = Table(
    "illustrations",
    metadata,
    Column("illustration_id", Integer, primary_key=True),
    Column("scene_id", Integer),
    Column("image_url", Text),
    Column("prompt_used", Text),
    Column("generation_model", String(100)),
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

character_visual_profiles_table = Table(
    "character_visual_profiles",
    metadata,
    Column("visual_profile_id", Integer, primary_key=True),
    Column("character_id", Integer),
    Column("reference_images", JSON),
    Column("visual_embedding", Text),
    Column("style_rules", JSON),
)


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
class WorldRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: int | None
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
class IllustrationRecord:
    illustration_id: int
    scene_id: int | None
    image_url: str | None
    prompt_used: str | None
    generation_model: str | None
    generated_at: datetime | None


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
class CharacterVisualProfileRecord:
    visual_profile_id: int
    character_id: int | None
    reference_images: Any
    visual_embedding: str | None
    style_rules: Any


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


def _to_illustration(row) -> IllustrationRecord | None:
    if row is None:
        return None
    return IllustrationRecord(
        illustration_id=row.illustration_id,
        scene_id=row.scene_id,
        image_url=row.image_url,
        prompt_used=row.prompt_used,
        generation_model=row.generation_model,
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


def _to_visual_profile(row) -> CharacterVisualProfileRecord | None:
    if row is None:
        return None
    return CharacterVisualProfileRecord(
        visual_profile_id=row.visual_profile_id,
        character_id=row.character_id,
        reference_images=row.reference_images,
        visual_embedding=row.visual_embedding,
        style_rules=row.style_rules,
    )


def _extract_scene_payload(scene: SceneRecord) -> dict[str, Any]:
    if scene.scene_text is None or not scene.scene_text.strip():
        return {}
    try:
        payload = json.loads(scene.scene_text)
    except json.JSONDecodeError:
        return {"scene_text": scene.scene_text.strip()}
    if isinstance(payload, dict):
        return payload
    return {}


def get_story_for_account(db: Session, story_id: int, account_id: int) -> StoryRecord:
    row = db.execute(
        select(stories_generated_table)
        .select_from(
            stories_generated_table.join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(
            and_(
                stories_generated_table.c.story_id == story_id,
                readers_table.c.account_id == account_id,
            )
        )
    ).mappings().first()

    story = _to_story(row)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found",
        )
    return story


def get_story_scenes(db: Session, story_id: int) -> list[SceneRecord]:
    rows = db.execute(
        select(story_scenes_table)
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
    ).mappings().all()

    scenes = [_to_scene(row) for row in rows if _to_scene(row) is not None]
    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story has no scenes",
        )
    return scenes


def get_story_world(db: Session, story: StoryRecord) -> WorldRecord:
    if story.reader_world_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story has no associated reader world",
        )

    row = db.execute(
        select(worlds_table)
        .select_from(
            reader_worlds_table.join(
                worlds_table,
                reader_worlds_table.c.world_id == worlds_table.c.world_id,
            )
        )
        .where(reader_worlds_table.c.reader_world_id == story.reader_world_id)
    ).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    world = _to_world(row)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return world


def list_story_world_characters(db: Session, story: StoryRecord) -> list[CharacterRecord]:
    if story.reader_world_id is None:
        return []
    rows = db.execute(
        select(characters_table)
        .select_from(
            characters_table.join(
                reader_worlds_table,
                characters_table.c.world_id == reader_worlds_table.c.world_id,
            )
        )
        .where(reader_worlds_table.c.reader_world_id == story.reader_world_id)
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()
    return [_to_character(row) for row in rows if _to_character(row) is not None]


def get_location_for_character(db: Session, location_id: int | None) -> LocationRecord | None:
    if location_id is None:
        return None
    row = db.execute(
        select(locations_table).where(locations_table.c.location_id == location_id)
    ).mappings().first()
    return _to_location(row)


def list_scene_referenced_characters(
    db: Session,
    scene: SceneRecord,
    story_characters: list[CharacterRecord],
) -> list[CharacterRecord]:
    payload = _extract_scene_payload(scene)
    searchable_parts: list[str] = []

    illustration_prompt = payload.get("illustration_prompt")
    if isinstance(illustration_prompt, str) and illustration_prompt.strip():
        searchable_parts.append(illustration_prompt.strip())

    paragraphs = payload.get("paragraphs")
    if isinstance(paragraphs, list):
        searchable_parts.extend(
            paragraph.strip()
            for paragraph in paragraphs
            if isinstance(paragraph, str) and paragraph.strip()
        )

    scene_text = payload.get("scene_text")
    if isinstance(scene_text, str) and scene_text.strip():
        searchable_parts.append(scene_text.strip())

    combined_text = " ".join(searchable_parts).lower()
    if not combined_text:
        return []

    referenced: list[CharacterRecord] = []
    for character in story_characters:
        if not character.name:
            continue
        if character.name.lower() in combined_text:
            referenced.append(character)
    return referenced


def build_scene_prompt_seed(scene: SceneRecord) -> dict[str, Any]:
    payload = _extract_scene_payload(scene)
    prompt_value = payload.get("illustration_prompt")
    scene_text_value = payload.get("scene_text")
    paragraphs_value = payload.get("paragraphs")
    return {
        "illustration_prompt": prompt_value.strip() if isinstance(prompt_value, str) and prompt_value.strip() else None,
        "scene_text": scene_text_value.strip() if isinstance(scene_text_value, str) and scene_text_value.strip() else None,
        "paragraphs": [
            paragraph.strip()
            for paragraph in paragraphs_value
            if isinstance(paragraph, str) and paragraph.strip()
        ] if isinstance(paragraphs_value, list) else [],
    }


def get_character_visual_profile(db: Session, character_id: int) -> CharacterVisualProfileRecord | None:
    row = db.execute(
        select(character_visual_profiles_table)
        .where(character_visual_profiles_table.c.character_id == character_id)
        .order_by(character_visual_profiles_table.c.visual_profile_id.asc())
    ).mappings().first()
    return _to_visual_profile(row)


def upsert_character_visual_profile(
    db: Session,
    character_id: int,
    reference_images: list[str],
    style_rules: dict[str, Any],
) -> CharacterVisualProfileRecord:
    existing = db.execute(
        select(character_visual_profiles_table)
        .where(character_visual_profiles_table.c.character_id == character_id)
        .order_by(character_visual_profiles_table.c.visual_profile_id.asc())
    ).mappings().first()

    if existing is None:
        result = db.execute(
            character_visual_profiles_table.insert().values(
                character_id=character_id,
                reference_images=reference_images,
                visual_embedding=None,
                style_rules=style_rules,
            )
        )
        visual_profile_id = int(result.inserted_primary_key[0])
    else:
        db.execute(
            character_visual_profiles_table.update()
            .where(character_visual_profiles_table.c.visual_profile_id == existing["visual_profile_id"])
            .values(
                reference_images=reference_images,
                style_rules=style_rules,
            )
        )
        visual_profile_id = int(existing["visual_profile_id"])

    row = db.execute(
        select(character_visual_profiles_table)
        .where(character_visual_profiles_table.c.visual_profile_id == visual_profile_id)
    ).mappings().first()
    profile = _to_visual_profile(row)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Character visual profile could not be stored",
        )
    return profile


def upsert_scene_illustration(
    db: Session,
    scene_id: int,
    image_url: str,
    prompt_used: str,
    generation_model: str,
) -> IllustrationRecord:
    existing = db.execute(
        select(illustrations_table).where(illustrations_table.c.scene_id == scene_id)
    ).mappings().first()

    if existing is None:
        result = db.execute(
            illustrations_table.insert().values(
                scene_id=scene_id,
                image_url=image_url,
                prompt_used=prompt_used,
                generation_model=generation_model,
            )
        )
        illustration_id = int(result.inserted_primary_key[0])
    else:
        db.execute(
            illustrations_table.update()
            .where(illustrations_table.c.illustration_id == existing["illustration_id"])
            .values(
                image_url=image_url,
                prompt_used=prompt_used,
                generation_model=generation_model,
            )
        )
        illustration_id = int(existing["illustration_id"])

    row = db.execute(
        select(illustrations_table).where(illustrations_table.c.illustration_id == illustration_id)
    ).mappings().first()
    illustration = _to_illustration(row)
    if illustration is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Illustration metadata could not be stored",
        )
    return illustration


def update_scene_illustration_url(
    db: Session,
    scene_id: int,
    illustration_url: str,
) -> SceneRecord:
    db.execute(
        story_scenes_table.update()
        .where(story_scenes_table.c.scene_id == scene_id)
        .values(illustration_url=illustration_url)
    )
    row = db.execute(
        select(story_scenes_table).where(story_scenes_table.c.scene_id == scene_id)
    ).mappings().first()
    scene = _to_scene(row)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scene illustration could not be updated",
        )
    return scene


def insert_scene_version_snapshot(db: Session, scene: SceneRecord) -> None:
    max_version_row = db.execute(
        select(func.max(scene_versions_table.c.version_number).label("max_version"))
        .where(scene_versions_table.c.scene_id == scene.scene_id)
    ).mappings().first()
    next_version = 1 if max_version_row is None or max_version_row.max_version is None else int(max_version_row.max_version) + 1

    db.execute(
        scene_versions_table.insert().values(
            scene_id=scene.scene_id,
            version_number=next_version,
            scene_text=scene.scene_text,
            illustration_url=scene.illustration_url,
            audio_url=scene.audio_url,
        )
    )


def list_story_illustrations(db: Session, story_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        select(
            story_scenes_table.c.scene_id,
            story_scenes_table.c.scene_order,
            illustrations_table.c.image_url,
            illustrations_table.c.prompt_used,
            illustrations_table.c.generation_model,
            illustrations_table.c.generated_at,
        )
        .select_from(
            story_scenes_table.outerjoin(
                illustrations_table,
                story_scenes_table.c.scene_id == illustrations_table.c.scene_id,
            )
        )
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
    ).mappings().all()
    return [dict(row) for row in rows]


def get_story_illustration(db: Session, story_id: int) -> IllustrationRecord | None:
    row = db.execute(
        select(illustrations_table)
        .select_from(
            illustrations_table.join(
                story_scenes_table,
                illustrations_table.c.scene_id == story_scenes_table.c.scene_id,
            )
        )
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), illustrations_table.c.illustration_id.asc())
    ).mappings().first()

    return _to_illustration(row)
