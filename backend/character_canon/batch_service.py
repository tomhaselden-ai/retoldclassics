from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.character_canon.enhancement_service import generate_character_canon_preview
from backend.character_canon.repository import get_character_canon_profile
from backend.character_canon.service import publish_reader_world_character_canon
from backend.config.settings import OPENAI_API_KEY
from backend.readers.reader_learning_model import readers_table
from backend.readers.reader_service import list_readers
from backend.worlds.world_service import create_reader_world_relationship, list_reader_worlds
from backend.worlds.reader_world_context import load_reader_world_context


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class RelationshipSuggestion(BaseModel):
    character_a_name: str = Field(min_length=1, max_length=255)
    character_b_name: str = Field(min_length=1, max_length=255)
    relationship_type: str = Field(min_length=1, max_length=100)
    relationship_strength: int = Field(ge=0, le=10)
    rationale: str | None = None


class RelationshipSuggestionPackage(BaseModel):
    relationships: list[RelationshipSuggestion] = Field(default_factory=list)


@dataclass
class CharacterBatchResult:
    character_id: int
    name: str | None
    status: str
    canon_version: int | None = None
    source_status: str | None = None
    error: str | None = None


def list_account_ids_with_readers(db: Session) -> list[int]:
    rows = db.execute(
        select(readers_table.c.account_id).distinct().order_by(readers_table.c.account_id.asc())
    ).all()
    return [int(row[0]) for row in rows if row and row[0] is not None]


def _pair_key(character_a_id: int, character_b_id: int) -> tuple[int, int]:
    return tuple(sorted((character_a_id, character_b_id)))


def _sanitize_relationship_suggestions(
    relationships: list[dict[str, Any]],
    *,
    name_to_id: dict[str, int],
    existing_pairs: set[tuple[int, int]],
) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen_pairs = set(existing_pairs)
    for item in relationships:
        character_a_name = str(item.get("character_a_name") or "").strip()
        character_b_name = str(item.get("character_b_name") or "").strip()
        if not character_a_name or not character_b_name:
            continue
        if character_a_name == character_b_name:
            continue
        if character_a_name not in name_to_id or character_b_name not in name_to_id:
            continue
        pair = _pair_key(name_to_id[character_a_name], name_to_id[character_b_name])
        if pair in seen_pairs:
            continue
        relationship_type = str(item.get("relationship_type") or "").strip()
        if not relationship_type:
            continue
        try:
            relationship_strength = int(item.get("relationship_strength") or 5)
        except (TypeError, ValueError):
            relationship_strength = 5
        relationship_strength = max(0, min(10, relationship_strength))
        cleaned.append(
            {
                "character_a_id": name_to_id[character_a_name],
                "character_b_id": name_to_id[character_b_name],
                "character_a_name": character_a_name,
                "character_b_name": character_b_name,
                "relationship_type": relationship_type,
                "relationship_strength": relationship_strength,
                "rationale": str(item.get("rationale") or "").strip() or None,
            }
        )
        seen_pairs.add(pair)
    return cleaned


def _build_relationship_messages(
    context: dict[str, Any],
    *,
    max_new_relationships: int,
) -> list[dict[str, str]]:
    character_payload = [
        {
            "name": character.name,
            "species": character.species,
            "personality_traits": character.personality_traits,
            "home_location": character.home_location,
        }
        for character in context["characters"]
    ]
    relationship_payload = [
        {
            "character_a": relationship.character_a,
            "character_b": relationship.character_b,
            "relationship_type": relationship.relationship_type,
            "relationship_strength": relationship.relationship_strength,
        }
        for relationship in context["relationships"]
    ]
    world_payload = {
        "name": getattr(context["world"], "name", None),
        "description": getattr(context["world"], "description", None),
        "world_rules": [
            {
                "rule_type": getattr(rule, "rule_type", None),
                "rule_description": getattr(rule, "rule_description", None),
            }
            for rule in context["world_rules"]
        ],
    }
    system_prompt = (
        "You are strengthening recurring children's story character relationships for a persistent story universe. "
        "Return strict JSON with a top-level 'relationships' array. "
        "Only suggest relationships between the provided characters. "
        "Do not duplicate existing relationships. "
        "Keep the results child-safe, emotionally coherent, and useful for future storytelling. "
        "Use relationship types like friend, sibling-like, mentor, protector, rival, helper, guide, teammate. "
        "Include a short rationale for each suggestion."
    )
    user_prompt = json.dumps(
        {
            "world": world_payload,
            "characters": character_payload,
            "existing_relationships": relationship_payload,
            "max_new_relationships": max_new_relationships,
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def suggest_reader_world_relationships(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    max_new_relationships: int = 4,
) -> list[dict[str, Any]]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured",
        )

    context = load_reader_world_context(
        db,
        next(
            reader_world.reader_world_id
            for reader_world in list_reader_worlds(db, account_id, reader_id)
            if reader_world.world_id == world_id
        ),
    )
    if len(context["characters"]) < 2:
        return []

    response = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "response_format": {"type": "json_object"},
            "messages": _build_relationship_messages(context, max_new_relationships=max_new_relationships),
            "temperature": 0.4,
        },
        timeout=60,
    )
    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Relationship enhancement failed: {response.text}",
        )

    content = response.json()["choices"][0]["message"]["content"]
    try:
        payload = json.loads(content)
        package = RelationshipSuggestionPackage.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Relationship enhancement returned invalid JSON",
        ) from exc

    name_to_id = {
        str(character.name).strip(): int(character.character_id)
        for character in context["characters"]
        if getattr(character, "name", None) and isinstance(getattr(character, "character_id", None), int)
    }
    existing_pairs = {
        _pair_key(int(relationship.character_a), int(relationship.character_b))
        for relationship in context["relationships"]
        if isinstance(relationship.character_a, int) and isinstance(relationship.character_b, int)
    }
    return _sanitize_relationship_suggestions(
        [item.model_dump() for item in package.relationships],
        name_to_id=name_to_id,
        existing_pairs=existing_pairs,
    )


def apply_reader_world_relationship_suggestions(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    suggestions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for item in suggestions:
        create_reader_world_relationship(
            db=db,
            account_id=account_id,
            reader_id=reader_id,
            template_world_id=world_id,
            character_a=int(item["character_a_id"]),
            character_b=int(item["character_b_id"]),
            relationship_type=str(item["relationship_type"]),
            relationship_strength=int(item["relationship_strength"]),
        )
        applied.append(item)
    return applied


def should_process_character(existing_canon: dict[str, Any] | None, *, force: bool) -> bool:
    if force:
        return True
    if existing_canon is None:
        return True
    if bool(existing_canon.get("is_locked")):
        return False
    return str(existing_canon.get("source_status") or "").strip().lower() != "canonical"


def enhance_reader_world_characters(
    db: Session,
    *,
    account_id: int,
    reader_id: int,
    world_id: int,
    apply_changes: bool,
    force: bool = False,
) -> list[CharacterBatchResult]:
    reader_worlds = list_reader_worlds(db, account_id, reader_id)
    reader_world = next((item for item in reader_worlds if item.world_id == world_id), None)
    if reader_world is None:
        return []

    context = load_reader_world_context(db, reader_world.reader_world_id)
    results: list[CharacterBatchResult] = []
    for character in context["characters"]:
        if not isinstance(getattr(character, "character_id", None), int):
            continue
        existing_canon = get_character_canon_profile(
            db,
            account_id=account_id,
            reader_world_id=reader_world.reader_world_id,
            character_id=character.character_id,
        )
        if not should_process_character(existing_canon, force=force):
            results.append(
                CharacterBatchResult(
                    character_id=character.character_id,
                    name=character.name,
                    status="skipped_locked_or_canonical",
                    canon_version=int(existing_canon["canon_version"]) if existing_canon and existing_canon.get("canon_version") else None,
                    source_status=str(existing_canon.get("source_status")) if existing_canon else None,
                )
            )
            continue

        try:
            preview = generate_character_canon_preview(
                db,
                account_id=account_id,
                reader_id=reader_id,
                world_id=world_id,
                character_id=character.character_id,
                section_mode="full",
                existing_canon=existing_canon,
                persist_run=apply_changes,
            )
            preview_profile = dict(preview["preview_profile"])
            enhancement_run = preview.get("enhancement_run") or {}

            if apply_changes:
                published = publish_reader_world_character_canon(
                    db,
                    account_id=account_id,
                    reader_id=reader_id,
                    world_id=world_id,
                    character_id=character.character_id,
                    updates=preview_profile,
                    enhanced_by=account_id,
                    enhancement_run_id=enhancement_run.get("enhancement_run_id"),
                )
                canon = published["canon"]
                results.append(
                    CharacterBatchResult(
                        character_id=character.character_id,
                        name=character.name,
                        status="published",
                        canon_version=int(canon.get("canon_version") or 0) or None,
                        source_status=str(canon.get("source_status") or "") or None,
                    )
                )
            else:
                results.append(
                    CharacterBatchResult(
                        character_id=character.character_id,
                        name=character.name,
                        status="previewed",
                        canon_version=int(preview_profile.get("canon_version") or 0) or None,
                        source_status=str(preview_profile.get("source_status") or "") or None,
                    )
                )
        except Exception as exc:  # pragma: no cover - batch guard
            if apply_changes:
                db.rollback()
            results.append(
                CharacterBatchResult(
                    character_id=character.character_id,
                    name=character.name,
                    status="failed",
                    error=str(exc),
                )
            )
    return results


def build_batch_scope(db: Session, *, reader_id: int | None = None, world_id: int | None = None) -> list[dict[str, Any]]:
    scope: list[dict[str, Any]] = []
    account_ids = list_account_ids_with_readers(db)
    for account_id in account_ids:
        readers = list_readers(db, account_id)
        for reader in readers:
            if reader_id is not None and reader.reader_id != reader_id:
                continue
            reader_worlds = list_reader_worlds(db, account_id, reader.reader_id)
            for reader_world in reader_worlds:
                if world_id is not None and reader_world.world_id != world_id:
                    continue
                scope.append(
                    {
                        "account_id": account_id,
                        "reader_id": reader.reader_id,
                        "reader_name": reader.name,
                        "reader_world_id": reader_world.reader_world_id,
                        "world_id": reader_world.world_id,
                        "world_name": reader_world.custom_name or reader_world.world.name,
                    }
                )
    return scope
