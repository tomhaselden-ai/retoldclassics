import json
from typing import Any

from backend.character_canon.prompt_packs import build_story_character_guidance


MAX_PROMPT_TOKENS = 4000


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _trim_to_token_budget(parts: list[str], token_budget: int) -> list[str]:
    selected: list[str] = []
    current_tokens = 0
    for part in parts:
        part_tokens = _estimate_tokens(part)
        if current_tokens + part_tokens > token_budget:
            break
        selected.append(part)
        current_tokens += part_tokens
    return selected


def build_story_prompt(
    reader_profile: Any,
    reader_world: Any,
    world_context: dict[str, Any],
    classical_chunks: list[dict[str, Any]],
    theme: str,
    target_length: str,
    required_story_character: dict[str, Any] | None = None,
    character_canon_lookup: dict[int, dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    characters_payload = [
        build_story_character_guidance(
            character,
            (character_canon_lookup or {}).get(character.character_id),
        )
        for character in world_context["characters"]
    ]

    locations_payload = [
        {
            "location_id": location.location_id,
            "name": location.name,
            "description": location.description,
        }
        for location in world_context["locations"]
    ]

    relationships_payload = [
        {
            "relationship_id": relationship.relationship_id,
            "character_a": relationship.character_a,
            "character_b": relationship.character_b,
            "relationship_type": relationship.relationship_type,
            "relationship_strength": relationship.relationship_strength,
        }
        for relationship in world_context["relationships"]
    ]

    chunk_parts = [
        json.dumps(
            {
                "story_id": chunk["metadata"].get("story_id"),
                "title": chunk["metadata"].get("title"),
                "themes": chunk["metadata"].get("themes"),
                "text_chunk": chunk["text_chunk"],
            },
            ensure_ascii=False,
        )
        for chunk in classical_chunks[:5]
    ]
    trimmed_chunks = _trim_to_token_budget(chunk_parts, 1800)

    prompt_payload = {
        "reader_profile": {
            "reader_id": reader_profile.reader_id,
            "age": reader_profile.age,
            "reading_level": reader_profile.reading_level,
            "trait_focus": reader_profile.trait_focus,
        },
        "reader_world": {
            "reader_world_id": reader_world.reader_world_id,
            "world_id": reader_world.world_id,
            "custom_name": reader_world.custom_name,
        },
        "world": {
            "world_id": world_context["world"].world_id,
            "name": world_context["world"].name,
            "description": world_context["world"].description,
        },
        "characters": characters_payload,
        "locations": locations_payload,
        "relationships": relationships_payload,
        "theme": theme,
        "target_length": target_length,
        "required_story_character": required_story_character,
        "classical_story_chunks": [json.loads(chunk) for chunk in trimmed_chunks],
    }

    user_content = json.dumps(prompt_payload, ensure_ascii=False)
    if _estimate_tokens(user_content) > MAX_PROMPT_TOKENS:
        raise ValueError("Prompt exceeds maximum size")

    return [
        {
            "role": "system",
            "content": (
                "You are a children's storyteller writing immersive stories.\n"
                "Use characters and locations from the world provided.\n"
                "If required_story_character is present, use that character as the protagonist "
                "or a central focal character.\n"
                "Use narrative inspiration from the classical story excerpts.\n"
                "Write a new original story.\n"
                "Do not copy classical stories.\n"
                "Return strict JSON with keys: title, summary, scenes.\n"
                "Each scene must contain: scene_title, beats, paragraphs, illustration_prompt."
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]
