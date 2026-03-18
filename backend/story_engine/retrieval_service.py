import json
from typing import Any

from fastapi import HTTPException, status

from backend.story_engine.vector_store import ClassicalStoryVectorStore


def _normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _flatten_traits(characters: list[Any]) -> list[str]:
    trait_values: list[str] = []
    for character in characters:
        personality_traits = _normalize_json(getattr(character, "personality_traits", None))
        if isinstance(personality_traits, list):
            for item in personality_traits:
                if isinstance(item, str) and item.strip():
                    trait_values.append(item.strip())
        elif isinstance(personality_traits, str) and personality_traits.strip():
            trait_values.append(personality_traits.strip())
    return trait_values


def build_retrieval_query(theme: str, reader_profile: Any, world_context: dict[str, Any]) -> str:
    character_traits = ", ".join(_flatten_traits(world_context["characters"]))
    location_names = ", ".join(
        location.name for location in world_context["locations"] if location.name
    )
    return (
        f"Theme: {theme}. "
        f"Reader age: {reader_profile.age}. "
        f"Reading level: {reader_profile.reading_level}. "
        f"Character traits: {character_traits}. "
        f"Story situation in locations: {location_names}."
    )


def retrieve_classical_guidance(
    theme: str,
    reader_profile: Any,
    world_context: dict[str, Any],
    vector_store: ClassicalStoryVectorStore | None = None,
) -> list[dict[str, Any]]:
    store = vector_store or ClassicalStoryVectorStore()
    query_text = build_retrieval_query(theme, reader_profile, world_context)
    chunks = store.query(query_text=query_text, top_k=5)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No classical story guidance was found for this request",
        )

    return chunks[:5]
