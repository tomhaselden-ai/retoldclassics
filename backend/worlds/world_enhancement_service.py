from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import requests
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.config.settings import OPENAI_API_KEY
from backend.worlds.world_enhancement_repository import (
    WorldContextRecord,
    load_world_context_for_enhancement,
    replace_world_content,
)


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class EnhancedWorld(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=80)

    @field_validator("description")
    @classmethod
    def require_three_paragraphs(cls, value: str) -> str:
        paragraphs = [part.strip() for part in value.split("\n\n") if part.strip()]
        if len(paragraphs) < 3:
            raise ValueError("world.description must contain at least 3 paragraphs")
        return value


class EnhancedLocation(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=20)


class EnhancedCharacter(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    species: str = Field(min_length=1, max_length=100)
    personality_traits: list[str] = Field(min_length=2, max_length=4)
    home_location_name: str = Field(min_length=1, max_length=255)


class EnhancedRelationship(BaseModel):
    character_a_name: str = Field(min_length=1, max_length=255)
    character_b_name: str = Field(min_length=1, max_length=255)
    relationship_type: str = Field(min_length=1, max_length=100)
    relationship_strength: int = Field(ge=0, le=10)


class EnhancedWorldRule(BaseModel):
    rule_type: str = Field(min_length=1, max_length=100)
    rule_description: str = Field(min_length=8)


class WorldEnhancementPackage(BaseModel):
    world: EnhancedWorld
    locations: list[EnhancedLocation] = Field(min_length=5, max_length=7)
    characters: list[EnhancedCharacter] = Field(min_length=6, max_length=8)
    relationships: list[EnhancedRelationship] = Field(min_length=5)
    world_rules: list[EnhancedWorldRule] = Field(min_length=3)


@dataclass
class WorldEnhancementResult:
    world_id: int
    applied: bool
    world_name: str
    summary: dict[str, int]
    package: dict[str, Any]


def _serialize_context(context: WorldContextRecord) -> dict[str, Any]:
    return {
        "world_id": context.world_id,
        "name": context.name,
        "description": context.description,
        "default_world": context.default_world,
        "locations": context.locations,
        "characters": context.characters,
        "relationships": context.relationships,
        "world_rules": context.world_rules,
    }


def _build_messages(context: WorldContextRecord) -> list[dict[str, str]]:
    context_payload = json.dumps(_serialize_context(context), ensure_ascii=False, indent=2)
    schema_example = {
        "world": {
            "name": context.name or "World Name",
            "description": "Paragraph one.\n\nParagraph two.\n\nParagraph three.",
        },
        "locations": [
            {"name": "Location Name", "description": "Location description."},
        ],
        "characters": [
            {
                "name": "Character Name",
                "species": "owl",
                "personality_traits": ["wise", "watchful", "gentle"],
                "home_location_name": "Location Name",
            }
        ],
        "relationships": [
            {
                "character_a_name": "Character Name",
                "character_b_name": "Second Character",
                "relationship_type": "mentor",
                "relationship_strength": 8,
            }
        ],
        "world_rules": [
            {"rule_type": "magic", "rule_description": "Magic rule description."},
        ],
    }
    system_prompt = (
        "You expand children's story worlds into rich, internally consistent world-building packages.\n"
        "Return JSON only. Do not add markdown. Do not omit required keys.\n"
        "Keep the world suitable for children and faithful to the world biome and tone already present.\n"
        "All characters, locations, and relationships must make sense for this world.\n"
        "Traits should fit the character and species naturally.\n"
        "Location and species choices must match the ecology of the world.\n"
        "Provide exactly these top-level keys: world, locations, characters, relationships, world_rules.\n"
        "Use names, not database ids. Do not return character_id, location_id, home_location, or relationship_id fields."
    )
    user_prompt = (
        "Enhance this existing story world.\n\n"
        "Requirements:\n"
        "- Keep the same world identity, but improve richness and coherence.\n"
        "- world.description must be at least 3 paragraphs.\n"
        "- Return 5 to 7 locations.\n"
        "- Return 6 to 8 characters.\n"
        "- Every character must have 2 to 4 personality traits and a valid home_location_name.\n"
        "- Return relationship records between the returned characters only.\n"
        "- Return at least 3 world rules.\n"
        "- Make the world more useful for future story generation.\n"
        "- Include a balanced mix of safe, mysterious, social, and risky places where appropriate.\n"
        "- Include a balanced mix of mentors, friends, rivals, timid characters, and bold characters where appropriate.\n\n"
        f"Required output schema example:\n{json.dumps(schema_example, ensure_ascii=False, indent=2)}\n\n"
        f"Current world context:\n{context_payload}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _call_openai(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured",
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
            "messages": messages,
            "temperature": 0.7,
        },
        timeout=60,
    )

    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API failed: {response.text}",
        )

    content = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI returned invalid JSON for world enhancement",
        ) from exc


def _normalize_characters(payload: dict[str, Any], context: WorldContextRecord) -> None:
    existing_location_names = {
        int(item["location_id"]): item["name"]
        for item in context.locations
        if isinstance(item.get("location_id"), int) and isinstance(item.get("name"), str)
    }

    characters = payload.get("characters")
    if not isinstance(characters, list):
        return

    for item in characters:
        if not isinstance(item, dict):
            continue
        if "home_location_name" not in item:
            home_location = item.get("home_location")
            if isinstance(home_location, int) and home_location in existing_location_names:
                item["home_location_name"] = existing_location_names[home_location]
            elif isinstance(home_location, str) and home_location.strip():
                item["home_location_name"] = home_location.strip()
        item.pop("character_id", None)
        item.pop("home_location", None)


def _normalize_relationships(payload: dict[str, Any], context: WorldContextRecord) -> None:
    existing_character_names = {
        int(item["character_id"]): item["name"]
        for item in context.characters
        if isinstance(item.get("character_id"), int) and isinstance(item.get("name"), str)
    }

    relationships = payload.get("relationships")
    if not isinstance(relationships, list):
        return

    for item in relationships:
        if not isinstance(item, dict):
            continue

        if "character_a_name" not in item or "character_b_name" not in item:
            referenced_ids: list[int] = []
            for key, value in item.items():
                if not isinstance(value, int):
                    continue
                if key in {"character_a", "character_b"} or key.startswith("character_id"):
                    referenced_ids.append(value)

            resolved_names = [existing_character_names[character_id] for character_id in referenced_ids if character_id in existing_character_names]
            if len(resolved_names) >= 2:
                item.setdefault("character_a_name", resolved_names[0])
                item.setdefault("character_b_name", resolved_names[1])

        if "relationship_strength" not in item:
            item["relationship_strength"] = 5

        for key in list(item.keys()):
            if key in {"relationship_id", "character_a", "character_b"} or re.match(r"character_id(_\d+)?$", key):
                item.pop(key, None)


def _normalize_payload(payload: dict[str, Any], context: WorldContextRecord) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    _normalize_characters(payload, context)
    _normalize_relationships(payload, context)
    return payload


def _validate_package(payload: dict[str, Any], context: WorldContextRecord) -> WorldEnhancementPackage:
    normalized_payload = _normalize_payload(payload, context)
    try:
        package = WorldEnhancementPackage.model_validate(normalized_payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"World enhancement validation failed: {exc}",
        ) from exc

    location_names = {item.name for item in package.locations}
    if len(location_names) != len(package.locations):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="World enhancement contains duplicate location names",
        )

    character_names = {item.name for item in package.characters}
    if len(character_names) != len(package.characters):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="World enhancement contains duplicate character names",
        )

    for character in package.characters:
        if character.home_location_name not in location_names:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Character home location is invalid: {character.home_location_name}",
            )

    for relationship in package.relationships:
        if relationship.character_a_name not in character_names or relationship.character_b_name not in character_names:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Relationship references an unknown character",
            )
        if relationship.character_a_name == relationship.character_b_name:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Relationship cannot target the same character on both sides",
            )

    return package


def _summary_for_package(package: WorldEnhancementPackage) -> dict[str, int]:
    return {
        "locations": len(package.locations),
        "characters": len(package.characters),
        "relationships": len(package.relationships),
        "world_rules": len(package.world_rules),
    }


def enhance_world(
    db: Session,
    world_id: int,
    apply_changes: bool = False,
) -> WorldEnhancementResult:
    context = load_world_context_for_enhancement(db, world_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")

    payload = _call_openai(_build_messages(context))
    package = _validate_package(payload, context)
    package_dump = package.model_dump()
    summary = _summary_for_package(package)

    if not apply_changes:
        return WorldEnhancementResult(
            world_id=world_id,
            applied=False,
            world_name=package.world.name,
            summary=summary,
            package=package_dump,
        )

    try:
        replace_summary = replace_world_content(db, world_id, package_dump)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="World enhancement could not be applied",
        ) from exc

    return WorldEnhancementResult(
        world_id=world_id,
        applied=True,
        world_name=package.world.name,
        summary=replace_summary,
        package=package_dump,
    )
