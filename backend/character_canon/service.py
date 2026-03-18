from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.character_canon.prompt_packs import (
    build_base_character_canon,
    finalize_character_canon,
    merge_character_canon_input,
)
from backend.character_canon.repository import (
    get_character_canon_profile,
    insert_character_canon_version,
    list_character_canon_enhancement_runs,
    list_character_canon_profiles,
    list_character_canon_versions,
    mark_character_canon_enhancement_run_applied,
    upsert_character_canon_profile,
)
from backend.continuity.continuity_repository import list_character_relationships_for_character
from backend.memory.event_repository import list_story_events_by_story
from backend.story_engine.story_repository import stories_generated_table
from backend.worlds.world_service import get_reader_world_context_for_account


def _resolve_reader_world_scope(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
) -> tuple[Any, dict[str, Any]]:
    context = get_reader_world_context_for_account(db, account_id, reader_id, world_id)
    reader_world = context["reader_world"]
    return reader_world, context


def _resolve_character_from_context(
    context: dict[str, Any],
    character_id: int,
) -> Any:
    character = next(
        (
            item
            for item in context["characters"]
            if getattr(item, "character_id", None) == character_id
        ),
        None,
    )
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found in this reader world",
        )
    return character


def _scoped_story_events_for_character(db: Session, reader_world_id: int, character_id: int) -> list[dict[str, Any]]:
    story_rows = db.execute(
        stories_generated_table.select()
        .where(stories_generated_table.c.reader_world_id == reader_world_id)
        .order_by(stories_generated_table.c.story_id.desc())
        .limit(12)
    ).mappings().all()
    events: list[dict[str, Any]] = []
    for story_row in story_rows:
        for event in list_story_events_by_story(db, story_row["story_id"]):
            if character_id in (getattr(event, "characters", None) or []):
                events.append(
                    {
                        "event_id": event.event_id,
                        "story_id": event.story_id,
                        "event_summary": event.event_summary,
                    }
                )
    return events[:10]


def list_reader_world_character_canon_overview(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
) -> dict[str, Any]:
    reader_world, context = _resolve_reader_world_scope(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
    )
    character_ids = [
        character.character_id
        for character in context["characters"]
        if isinstance(getattr(character, "character_id", None), int)
    ]
    canon_lookup = list_character_canon_profiles(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_ids=character_ids,
    )

    characters: list[dict[str, Any]] = []
    for character in context["characters"]:
        canon = canon_lookup.get(character.character_id)
        traits = character.personality_traits if isinstance(character.personality_traits, list) else []
        characters.append(
            {
                "character_id": character.character_id,
                "name": character.name,
                "species": character.species,
                "personality_traits": traits,
                "home_location": character.home_location,
                "canon_status": canon.get("source_status") if canon else "legacy",
                "canon_version": canon.get("canon_version") if canon else None,
                "is_locked": bool(canon.get("is_locked")) if canon else False,
                "is_major_character": bool(canon.get("is_major_character")) if canon else False,
                "last_reviewed_at": canon.get("last_reviewed_at") if canon else None,
                "enhanced_at": canon.get("enhanced_at") if canon else None,
            }
        )

    return {
        "reader_id": reader_id,
        "world_id": world_id,
        "reader_world_id": reader_world.reader_world_id,
        "world": {
            "world_id": context["world"].world_id,
            "name": context["world"].name,
            "description": context["world"].description,
        },
        "characters": characters,
    }


def get_reader_world_character_canon_detail(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    character_id: int,
) -> dict[str, Any]:
    reader_world, context = _resolve_reader_world_scope(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
    )
    character = _resolve_character_from_context(context, character_id)
    existing_canon = get_character_canon_profile(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
    )
    base_profile = build_base_character_canon(
        character=character,
        world=context["world"],
        reader_world_id=reader_world.reader_world_id,
        existing=existing_canon,
    )
    canon = finalize_character_canon(base_profile if existing_canon is None else merge_character_canon_input(base_profile, existing_canon))

    relationships = [
        {
            "relationship_id": relationship.relationship_id,
            "character_a": relationship.character_a,
            "character_b": relationship.character_b,
            "relationship_type": relationship.relationship_type,
            "relationship_strength": relationship.relationship_strength,
        }
        for relationship in context["relationships"]
        if relationship.character_a == character_id or relationship.character_b == character_id
    ]

    versions = list_character_canon_versions(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
    )
    enhancement_runs = list_character_canon_enhancement_runs(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
    )

    return {
        "reader_id": reader_id,
        "world_id": world_id,
        "reader_world_id": reader_world.reader_world_id,
        "world": {
            "world_id": context["world"].world_id,
            "name": context["world"].name,
            "description": context["world"].description,
        },
        "character": {
            "character_id": character.character_id,
            "world_id": character.world_id,
            "name": character.name,
            "species": character.species,
            "personality_traits": character.personality_traits,
            "home_location": character.home_location,
        },
        "canon": canon,
        "relationships": relationships,
        "world_rules": [
            {
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type,
                "rule_description": rule.rule_description,
            }
            for rule in context["world_rules"]
        ],
        "recent_memory_events": _scoped_story_events_for_character(db, reader_world.reader_world_id, character_id),
        "history": versions,
        "enhancement_runs": enhancement_runs,
    }


def _save_character_canon(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    character_id: int,
    updates: dict[str, Any],
    publish: bool,
    enhanced_by: int | None,
    enhancement_run_id: int | None,
) -> dict[str, Any]:
    reader_world, context = _resolve_reader_world_scope(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
    )
    character = _resolve_character_from_context(context, character_id)
    existing = get_character_canon_profile(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
    )
    base_profile = build_base_character_canon(
        character=character,
        world=context["world"],
        reader_world_id=reader_world.reader_world_id,
        existing=existing,
    )
    merged = finalize_character_canon(merge_character_canon_input(base_profile, updates))
    previous_version = int(existing["canon_version"]) if existing and existing.get("canon_version") else 0
    next_version = previous_version + 1
    merged["canon_version"] = next_version
    merged["enhanced_by"] = enhanced_by
    merged["enhanced_at"] = datetime.utcnow()
    merged["source_status"] = "canonical" if publish else (merged.get("source_status") or "enhanced")
    if publish:
        merged["last_reviewed_at"] = datetime.utcnow()

    stored = upsert_character_canon_profile(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
        profile=merged,
    )
    insert_character_canon_version(
        db,
        canon_id=stored["canon_id"],
        account_id=account_id,
        character_id=character_id,
        reader_world_id=reader_world.reader_world_id,
        canon_version=next_version,
        source_status=stored.get("source_status"),
        snapshot_json=stored,
        created_by=enhanced_by,
    )
    if enhancement_run_id is not None:
        mark_character_canon_enhancement_run_applied(db, enhancement_run_id=enhancement_run_id)

    db.commit()
    return get_reader_world_character_canon_detail(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
    )


def save_reader_world_character_canon(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    character_id: int,
    updates: dict[str, Any],
    enhanced_by: int | None,
    enhancement_run_id: int | None = None,
) -> dict[str, Any]:
    return _save_character_canon(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
        updates=updates,
        publish=False,
        enhanced_by=enhanced_by,
        enhancement_run_id=enhancement_run_id,
    )


def publish_reader_world_character_canon(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    character_id: int,
    updates: dict[str, Any],
    enhanced_by: int | None,
    enhancement_run_id: int | None = None,
) -> dict[str, Any]:
    return _save_character_canon(
        db,
        account_id=account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
        updates=updates,
        publish=True,
        enhanced_by=enhanced_by,
        enhancement_run_id=enhancement_run_id,
    )
