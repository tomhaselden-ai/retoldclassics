import re
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.memory.event_repository import insert_story_event
from backend.memory.vector_index_repository import insert_vector_index


EVENT_SOURCE_TYPE = "story_event"


def _alias_variants(name: str | None) -> list[str]:
    if not isinstance(name, str) or not name.strip():
        return []

    normalized = name.strip()
    variants = [normalized]
    if " of " in normalized:
        variants.append(normalized.split(" of ", 1)[0].strip())
    return [variant for variant in variants if variant]


def _text_contains_alias(text: str, alias: str) -> bool:
    return bool(re.search(rf"\b{re.escape(alias)}\b", text, flags=re.IGNORECASE))


def _searchable_scene_text(scene_payload: dict[str, Any]) -> str:
    searchable_parts = [
        scene_payload.get("scene_title"),
        scene_payload.get("illustration_prompt"),
        scene_payload.get("paragraphs"),
    ]
    beats = scene_payload.get("beats")
    if isinstance(beats, list):
        searchable_parts.extend(item for item in beats if isinstance(item, str))

    return " ".join(part.strip() for part in searchable_parts if isinstance(part, str) and part.strip())


def _resolve_character_ids(scene_payload: dict[str, Any], world_context: dict[str, Any]) -> list[int]:
    searchable_text = _searchable_scene_text(scene_payload)
    matched_ids: list[int] = []
    for character in world_context["characters"]:
        aliases = _alias_variants(character.name)
        if aliases and any(_text_contains_alias(searchable_text, alias) for alias in aliases):
            matched_ids.append(character.character_id)
    return matched_ids


def _resolve_location_id(scene_payload: dict[str, Any], world_context: dict[str, Any]) -> int | None:
    searchable_text = _searchable_scene_text(scene_payload)
    for location in world_context["locations"]:
        aliases = _alias_variants(location.name)
        if aliases and any(_text_contains_alias(searchable_text, alias) for alias in aliases):
            return location.location_id
    return None


def _scene_event_summaries(scene_payload: dict[str, Any]) -> list[str]:
    beats = scene_payload.get("beats")
    if isinstance(beats, list):
        summaries = [item.strip() for item in beats if isinstance(item, str) and item.strip()]
        if summaries:
            return summaries

    scene_title = scene_payload.get("scene_title")
    if isinstance(scene_title, str) and scene_title.strip():
        return [scene_title.strip()]

    paragraphs = scene_payload.get("paragraphs")
    if isinstance(paragraphs, str) and paragraphs.strip():
        first_sentence = paragraphs.strip().split(". ")[0].strip()
        if first_sentence:
            return [first_sentence.rstrip(".") + "."]

    return []


def capture_generated_story_events(
    db: Session,
    story_id: int,
    scenes: list[dict[str, Any]],
    world_context: dict[str, Any],
) -> int:
    inserted_count = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue

        character_ids = _resolve_character_ids(scene, world_context) or None
        location_id = _resolve_location_id(scene, world_context)
        summaries = _scene_event_summaries(scene)
        for summary in summaries:
            event = insert_story_event(
                db=db,
                story_id=story_id,
                characters=character_ids,
                location_id=location_id,
                event_summary=summary,
            )
            insert_vector_index(
                db=db,
                vector_id=uuid4().hex,
                source_type=EVENT_SOURCE_TYPE,
                source_id=event.event_id,
            )
            inserted_count += 1
    return inserted_count
