import logging
from collections import defaultdict
from typing import Any

from backend.classics.classics_repository import (
    count_classical_stories,
    get_classical_stories_by_ids,
    list_classical_stories,
)
from backend.classics.classics_serializer import (
    ALLOWED_AUTHORS,
    build_cover_metadata,
    expand_author_filters,
    extract_preview_text,
    normalize_author,
)
from backend.story_engine.vector_store import ClassicalStoryVectorStore


logger = logging.getLogger(__name__)

PROMPT_EXAMPLES = [
    "All Aesop stories about clever foxes",
    "Stories about patience",
    "Bedtime stories about kindness",
    "Stories about bravery and friendship",
]


def _build_story_item(story: Any) -> dict[str, Any]:
    return {
        "story_id": story.story_id,
        "title": story.title,
        "source_author": normalize_author(story.source_author),
        "age_range": story.age_range,
        "reading_level": story.reading_level,
        "preview_text": extract_preview_text(story),
        "cover": build_cover_metadata(story),
        "immersive_reader_available": True,
    }


def _rank_story_ids_from_chunks(
    chunks: list[dict[str, Any]],
    *,
    allowed_authors: set[str],
) -> list[int]:
    aggregate: dict[int, dict[str, float | int]] = defaultdict(lambda: {"hits": 0, "best_distance": 999999.0})

    for chunk in chunks:
        metadata = chunk.get("metadata") if isinstance(chunk, dict) else None
        if not isinstance(metadata, dict):
            continue

        story_id = metadata.get("story_id")
        author = normalize_author(str(metadata.get("author") or ""))
        if not isinstance(story_id, int) or story_id <= 0:
            continue
        if author is None or author not in allowed_authors:
            continue

        distance = chunk.get("distance")
        normalized_distance = float(distance) if isinstance(distance, (int, float)) else 999999.0
        aggregate[story_id]["hits"] = int(aggregate[story_id]["hits"]) + 1
        aggregate[story_id]["best_distance"] = min(float(aggregate[story_id]["best_distance"]), normalized_distance)

    ranked = sorted(
        aggregate.items(),
        key=lambda item: (-int(item[1]["hits"]), float(item[1]["best_distance"]), item[0]),
    )
    return [story_id for story_id, _ in ranked]


def _build_browse_payload(
    db: Any,
    authors: list[str],
    query_text: str | None,
    limit: int,
    offset: int,
    applied_author: str | None,
    *,
    match_mode: str,
) -> dict[str, Any]:
    stories = list_classical_stories(db, authors, query_text, limit, offset)
    total_count = count_classical_stories(db, authors, query_text)
    return {
        "items": [_build_story_item(story) for story in stories],
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "query": query_text,
        "applied_author": applied_author,
        "match_mode": match_mode,
        "prompt_examples": PROMPT_EXAMPLES,
    }


def discover_classics(
    db: Any,
    *,
    authors: list[str] | None = None,
    query_text: str | None,
    limit: int,
    offset: int,
    applied_author: str | None = None,
) -> dict[str, Any]:
    resolved_authors = authors or expand_author_filters(list(ALLOWED_AUTHORS))
    normalized_author_set = {
        normalized
        for normalized in (normalize_author(author) for author in resolved_authors)
        if normalized is not None
    }

    if not query_text:
        return _build_browse_payload(
            db,
            resolved_authors,
            None,
            limit,
            offset,
            applied_author,
            match_mode="browse",
        )

    try:
        store = ClassicalStoryVectorStore()
        semantic_chunks = store.query(query_text=query_text, top_k=max(limit + offset + 8, 12))
        ranked_story_ids = _rank_story_ids_from_chunks(semantic_chunks, allowed_authors=normalized_author_set)
        ranked_stories = get_classical_stories_by_ids(db, ranked_story_ids, resolved_authors)
        if ranked_stories:
            visible_stories = ranked_stories[offset : offset + limit]
            return {
                "items": [_build_story_item(story) for story in visible_stories],
                "total_count": len(ranked_stories),
                "limit": limit,
                "offset": offset,
                "query": query_text,
                "applied_author": applied_author,
                "match_mode": "semantic",
                "prompt_examples": PROMPT_EXAMPLES,
            }
    except Exception:
        logger.exception("semantic classics discovery unavailable; falling back to keyword search")

    return _build_browse_payload(
        db,
        resolved_authors,
        query_text,
        limit,
        offset,
        applied_author,
        match_mode="keyword_fallback",
    )
