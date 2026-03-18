import logging
import os
import json
import re
from typing import Any

import requests

from backend.config.settings import OPENAI_API_KEY
from backend.worlds.reader_world_context import CharacterRecord, create_reader_world_character


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
COMMON_SPECIES = {
    "bird",
    "chicken",
    "fox",
    "snail",
    "owl",
    "rabbit",
    "turtle",
    "fish",
    "frog",
    "squirrel",
    "monkey",
    "jaguar",
    "parrot",
    "sparrow",
    "dolphin",
    "octopus",
    "gorilla",
    "bear",
    "deer",
    "wolf",
}
IGNORED_TRAIT_WORDS = {
    "a",
    "an",
    "the",
    "about",
    "make",
    "tell",
    "story",
    "who",
    "that",
    "and",
    "with",
    "named",
}
TRAIT_HINTS = {
    "couldn't lie": "honest",
    "could not lie": "honest",
    "learned to fly": "determined",
    "learns to fly": "determined",
    "gets her nerve": "brave",
    "finds her nerve": "brave",
    "finds his nerve": "brave",
}


def _normalize_traits(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip().lower()]
    return []


def _character_matches_request(character: CharacterRecord, request_payload: dict[str, Any]) -> bool:
    requested_name = str(request_payload.get("requested_name") or "").strip().lower()
    requested_species = str(request_payload.get("species") or "").strip().lower()
    requested_traits = _normalize_traits(request_payload.get("personality_traits"))

    character_name = (character.name or "").strip().lower()
    character_species = (character.species or "").strip().lower()
    character_traits = _normalize_traits(character.personality_traits)

    if requested_name and character_name == requested_name:
        return True

    if requested_species and character_species != requested_species:
        return False

    if requested_traits:
        return all(trait in character_traits for trait in requested_traits)

    return bool(requested_species)


def _species_candidates(world_context: dict[str, Any]) -> set[str]:
    values = set(COMMON_SPECIES)
    for character in world_context["characters"]:
        if character.species and character.species.strip():
            values.add(character.species.strip().lower())
    return values


def _existing_species(world_context: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for character in world_context["characters"]:
        if character.species and character.species.strip():
            values.add(character.species.strip().lower())
    return values


def _infer_traits(text: str, prefix_tokens: list[str]) -> list[str]:
    traits: list[str] = []
    for phrase, trait in TRAIT_HINTS.items():
        if phrase in text.lower():
            traits.append(trait)
    for token in prefix_tokens[-3:]:
        normalized = token.strip().lower()
        if normalized and normalized not in IGNORED_TRAIT_WORDS and normalized not in traits:
            traits.append(normalized)
    if not traits:
        traits = ["curious", "kind"]
    elif len(traits) == 1:
        traits.append("curious")
    return traits[:4]


def _extract_requested_character_rule_based(theme: str, world_context: dict[str, Any]) -> dict[str, Any] | None:
    species_values = sorted(_species_candidates(world_context), key=len, reverse=True)
    if not species_values:
        return None

    pattern = re.compile(
        r"\b(?:a|an)\s+(?P<prefix>[a-z][a-z\s'-]*?)?\s*(?P<species>"
        + "|".join(re.escape(species) for species in species_values)
        + r")\b(?:\s+named\s+(?P<name>[A-Z][a-zA-Z'-]*))?",
        flags=re.IGNORECASE,
    )
    matches = list(pattern.finditer(theme))
    if not matches:
        return None

    existing_species = _existing_species(world_context)
    chosen_match = None
    for match in matches:
        species = match.group("species").strip().lower()
        if species not in existing_species:
            chosen_match = match
            break
    if chosen_match is None:
        chosen_match = matches[0]

    species = chosen_match.group("species").strip()
    requested_name = (chosen_match.group("name") or "").strip()
    prefix_tokens = [token for token in (chosen_match.group("prefix") or "").split() if token.strip()]
    personality_traits = _infer_traits(theme, prefix_tokens)

    home_location_name = None
    if world_context["locations"]:
        home_location_name = world_context["locations"][0].name

    return {
        "has_character_request": True,
        "requested_name": requested_name or None,
        "suggested_name": requested_name or f"{species.title()} Friend",
        "species": species.title(),
        "personality_traits": personality_traits,
        "home_location_name": home_location_name,
        "story_role": "protagonist",
    }


def _extract_requested_character(theme: str, world_context: dict[str, Any]) -> dict[str, Any] | None:
    rule_based = _extract_requested_character_rule_based(theme, world_context)
    if rule_based is not None:
        return rule_based

    if not OPENAI_API_KEY:
        return None

    existing_characters = [
        {
            "name": character.name,
            "species": character.species,
            "personality_traits": character.personality_traits,
        }
        for character in world_context["characters"]
    ]
    locations = [location.name for location in world_context["locations"] if location.name]

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
                {
                    "role": "system",
                    "content": (
                        "You extract whether a story request requires a specific character.\n"
                        "Return strict JSON with keys: has_character_request, requested_name, "
                        "suggested_name, species, personality_traits, home_location_name, story_role.\n"
                        "Only set has_character_request to true when the request clearly implies "
                        "a protagonist or important character.\n"
                        "Use 2 to 4 short personality traits.\n"
                        "Choose home_location_name only from the provided locations when possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Story request: {theme}\n"
                        f"World name: {world_context['world'].name or ''}\n"
                        f"World description: {world_context['world'].description or ''}\n"
                        f"Existing characters: {existing_characters}\n"
                        f"Available locations: {locations}\n"
                    ),
                },
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )

    if not response.ok:
        logging.warning("character extraction request failed: %s", response.text)
        return None

    try:
        payload = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(payload)
    except Exception:
        logging.warning("character extraction returned invalid JSON")
        return None

    if not isinstance(parsed, dict) or not parsed.get("has_character_request"):
        return None
    return parsed


def resolve_required_story_character(
    db,
    reader_world_id: int,
    theme: str,
    world_context: dict[str, Any],
) -> dict[str, Any] | None:
    request_payload = _extract_requested_character(theme, world_context)
    if not request_payload:
        return None

    for character in world_context["characters"]:
        if _character_matches_request(character, request_payload):
            return {
                "character_id": character.character_id,
                "name": character.name,
                "species": character.species,
                "personality_traits": character.personality_traits,
                "home_location": character.home_location,
                "story_role": request_payload.get("story_role"),
                "created": False,
            }

    species = str(request_payload.get("species") or "").strip()
    if not species:
        return None

    personality_traits = [
        str(item).strip()
        for item in request_payload.get("personality_traits", [])
        if str(item).strip()
    ]
    if not personality_traits:
        return None

    home_location_name = str(request_payload.get("home_location_name") or "").strip().lower()
    home_location_id = None
    for location in world_context["locations"]:
        if location.name and location.name.strip().lower() == home_location_name:
            home_location_id = location.location_id
            break
    if home_location_id is None and world_context["locations"]:
        home_location_id = world_context["locations"][0].location_id

    character_name = (
        str(request_payload.get("requested_name") or "").strip()
        or str(request_payload.get("suggested_name") or "").strip()
        or f"{species.title()} Friend"
    )

    created_character = create_reader_world_character(
        db=db,
        reader_world_id=reader_world_id,
        name=character_name,
        species=species,
        personality_traits=personality_traits,
        home_location=home_location_id,
    )
    return {
        "character_id": created_character.character_id,
        "name": created_character.name,
        "species": created_character.species,
        "personality_traits": created_character.personality_traits,
        "home_location": created_character.home_location,
        "story_role": request_payload.get("story_role"),
        "created": True,
    }
