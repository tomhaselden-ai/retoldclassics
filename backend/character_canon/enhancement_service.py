from __future__ import annotations

import json
import os
from typing import Any

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.character_canon.prompt_packs import (
    build_base_character_canon,
    finalize_character_canon,
    merge_character_canon_input,
)
from backend.character_canon.repository import get_character_canon_profile, insert_character_canon_enhancement_run
from backend.config.settings import OPENAI_API_KEY
from backend.memory.event_repository import list_story_events_by_story
from backend.story_engine.story_repository import stories_generated_table
from backend.worlds.world_service import get_reader_world_context_for_account


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


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
            characters = getattr(event, "characters", None) or []
            if character_id in characters:
                events.append(
                    {
                        "event_id": event.event_id,
                        "story_id": event.story_id,
                        "event_summary": event.event_summary,
                    }
                )
    return events[:10]


def _summarize_relationships(relationships: list[Any], character_lookup: dict[int, Any]) -> list[dict[str, Any]]:
    summarized: list[dict[str, Any]] = []
    for relationship in relationships:
        other_character_id = relationship.character_b if relationship.character_a in character_lookup else relationship.character_a
        other_character = character_lookup.get(other_character_id)
        summarized.append(
            {
                "relationship_type": relationship.relationship_type,
                "relationship_strength": relationship.relationship_strength,
                "other_character_name": getattr(other_character, "name", None),
            }
        )
    return summarized


def _build_ai_context(
    *,
    db: Session,
    character: Any,
    world_context: dict[str, Any],
    existing_canon: dict[str, Any] | None,
    reader_world_id: int,
) -> dict[str, Any]:
    world = world_context["world"]
    character_lookup = {
        item.character_id: item
        for item in world_context["characters"]
        if isinstance(getattr(item, "character_id", None), int)
    }
    related_relationships = [
        relationship
        for relationship in world_context["relationships"]
        if relationship.character_a == character.character_id or relationship.character_b == character.character_id
    ]
    memory_events = _scoped_story_events_for_character(db, reader_world_id, character.character_id)
    return {
        "world": {
            "world_id": getattr(world, "world_id", None),
            "name": getattr(world, "name", None),
            "description": getattr(world, "description", None),
        },
        "world_rules": [
            {
                "rule_type": getattr(rule, "rule_type", None),
                "rule_description": getattr(rule, "rule_description", None),
            }
            for rule in world_context["world_rules"]
        ],
        "locations": [
            {
                "location_id": getattr(location, "location_id", None),
                "name": getattr(location, "name", None),
                "description": getattr(location, "description", None),
            }
            for location in world_context["locations"]
        ],
        "character": {
            "character_id": getattr(character, "character_id", None),
            "name": getattr(character, "name", None),
            "species": getattr(character, "species", None),
            "personality_traits": getattr(character, "personality_traits", None),
            "home_location": getattr(character, "home_location", None),
        },
        "existing_canon": existing_canon,
        "relationships": _summarize_relationships(related_relationships, character_lookup),
        "recent_memory_events": memory_events,
    }


def _extract_generated_profile(content: str) -> dict[str, Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Character enhancement returned invalid JSON",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Character enhancement returned invalid payload",
        )
    return payload


def _call_openai_character_enhancement(
    *,
    section_mode: str,
    ai_context: dict[str, Any],
) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured",
        )

    system_prompt = (
        "You are enhancing a recurring children's story character into a structured canonical profile. "
        "Respect the existing role, world tone, child-safe storytelling, and persistent continuity. "
        "Return strict JSON with keys narrative, visual, metadata. "
        "narrative must include: role_in_world, age_category, gender_presentation, archetype, one_sentence_essence, "
        "full_personality_summary, dominant_traits, secondary_traits, core_motivations, fears_and_vulnerabilities, "
        "moral_tendencies, behavioral_rules_usually, behavioral_rules_never, behavioral_rules_requires_justification, "
        "speech_style, signature_expressions, relationship_tendencies, growth_arc_pattern, continuity_anchors. "
        "visual must include: visual_summary, form_type, anthropomorphic_level, size_and_proportions, silhouette_description, "
        "facial_features, eye_description, fur_skin_surface_description, hair_feather_tail_details, clothing_and_accessories, "
        "signature_physical_features, expression_range, movement_pose_tendencies, color_palette, art_style_constraints, "
        "visual_must_never_change, visual_may_change. "
        "metadata must include: is_major_character, notes. "
        "Use arrays for list-like fields. Keep the character grounded and internally consistent."
    )

    response = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "section_mode": section_mode,
                            "character_context": ai_context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0.4,
        },
        timeout=60,
    )

    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Character enhancement failed: {response.text}",
        )

    content = response.json()["choices"][0]["message"]["content"]
    return _extract_generated_profile(content)


def _flatten_ai_profile(
    ai_profile: dict[str, Any],
    *,
    base_profile: dict[str, Any],
    section_mode: str,
) -> dict[str, Any]:
    narrative = ai_profile.get("narrative") if isinstance(ai_profile.get("narrative"), dict) else {}
    visual = ai_profile.get("visual") if isinstance(ai_profile.get("visual"), dict) else {}
    metadata = ai_profile.get("metadata") if isinstance(ai_profile.get("metadata"), dict) else {}

    updates: dict[str, Any] = {}
    if section_mode in {"full", "narrative"}:
        updates.update(narrative)
    if section_mode in {"full", "visual"}:
        updates.update(visual)
    updates.update(metadata)
    updates["source_status"] = "enhanced"

    return finalize_character_canon(merge_character_canon_input(base_profile, updates))


def generate_character_canon_preview(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    character_id: int,
    section_mode: str,
    existing_canon: dict[str, Any] | None,
    persist_run: bool = True,
) -> dict[str, Any]:
    world_context = get_reader_world_context_for_account(db, account_id, reader_id, world_id)
    reader_world = world_context["reader_world"]

    character = next(
        (
            item
            for item in world_context["characters"]
            if getattr(item, "character_id", None) == character_id
        ),
        None,
    )
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found in this reader world",
        )

    scoped_existing_canon = existing_canon or get_character_canon_profile(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_id=character_id,
    )

    base_profile = build_base_character_canon(
        character=character,
        world=world_context["world"],
        reader_world_id=reader_world.reader_world_id,
        existing=scoped_existing_canon,
    )
    ai_context = _build_ai_context(
        db=db,
        character=character,
        world_context=world_context,
        existing_canon=scoped_existing_canon,
        reader_world_id=reader_world.reader_world_id,
    )
    generated = _call_openai_character_enhancement(section_mode=section_mode, ai_context=ai_context)
    preview_profile = _flatten_ai_profile(generated, base_profile=base_profile, section_mode=section_mode)

    run = None
    if persist_run:
        run = insert_character_canon_enhancement_run(
            db,
            account_id=account_id,
            character_id=character_id,
            world_id=world_id,
            reader_world_id=reader_world.reader_world_id,
            section_mode=section_mode,
            status="previewed",
            prompt_context_json=ai_context,
            generated_profile_json=preview_profile,
        )
    return {
        "enhancement_run": run,
        "preview_profile": preview_profile,
    }
