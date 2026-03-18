from typing import Any

from sqlalchemy.orm import Session

from backend.analytics.analytics_service import (
    get_account_learning_insights,
    get_reader_learning_insights,
)
from backend.dashboard.dashboard_service import get_reader_dashboard
from backend.library.library_service import get_reader_library
from backend.readers.reader_service import get_reader, list_readers
from backend.worlds.world_service import list_reader_worlds


def _normalize_trait_focus(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def get_parent_summary(db: Session, account_id: int) -> dict[str, Any]:
    readers = list_readers(db, account_id)
    learning_insights = get_account_learning_insights(db, account_id, account_id)
    readers_by_id = {reader.reader_id: reader for reader in readers}

    summary_readers: list[dict[str, Any]] = []
    for reader_insight in learning_insights["readers"]:
        reader = readers_by_id.get(reader_insight["reader_id"])
        focus_areas = reader_insight.get("focus_areas") or []
        recommendations = reader_insight.get("recommendations") or {}

        summary_readers.append(
            {
                "reader_id": reader_insight["reader_id"],
                "name": reader_insight.get("name") if reader is None else reader.name,
                "age": None if reader is None else reader.age,
                "reading_level": reader_insight.get("reading_level") if reader is None else reader.reading_level,
                "trait_focus": [] if reader is None else _normalize_trait_focus(reader.trait_focus),
                "proficiency": reader_insight.get("proficiency"),
                "stories_read": reader_insight.get("stories_read", 0),
                "words_mastered": reader_insight.get("words_mastered", 0),
                "average_game_score": reader_insight.get("average_game_score"),
                "strengths": reader_insight.get("strengths") or [],
                "focus_message": focus_areas[0]["message"] if focus_areas else None,
                "recommended_story_difficulty": recommendations.get("recommended_story_difficulty"),
                "recommended_vocabulary_difficulty": recommendations.get("recommended_vocabulary_difficulty"),
                "recommended_game_difficulty": recommendations.get("recommended_game_difficulty"),
            }
        )

    return {
        "account_id": account_id,
        "reader_count": learning_insights["reader_count"],
        "aggregate_statistics": learning_insights["aggregate_statistics"],
        "readers": summary_readers,
    }


def get_parent_reader_summary(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    reader = get_reader(db, account_id, reader_id)
    dashboard = get_reader_dashboard(db, account_id, reader_id)
    learning_insights = get_reader_learning_insights(db, account_id, reader_id)
    library = get_reader_library(db, account_id, reader_id)
    worlds = list_reader_worlds(db, account_id, reader_id)

    return {
        "reader": {
            "reader_id": reader.reader_id,
            "account_id": reader.account_id,
            "name": reader.name,
            "age": reader.age,
            "reading_level": reader.reading_level,
            "gender_preference": reader.gender_preference,
            "trait_focus": _normalize_trait_focus(reader.trait_focus),
            "created_at": reader.created_at,
        },
        "dashboard": dashboard,
        "learning_insights": learning_insights,
        "library_summary": {
            "bookshelf_id": library["bookshelf_id"],
            "story_count": library["story_count"],
            "recent_stories": library["stories"][:5],
        },
        "world_summary": {
            "world_count": len(worlds),
            "worlds": [
                {
                    "reader_world_id": world.reader_world_id,
                    "world_id": world.world_id,
                    "custom_name": world.custom_name,
                    "name": world.world.name,
                    "description": world.world.description,
                }
                for world in worlds
            ],
        },
    }
