from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.adaptive.adaptive_service import get_adaptive_profile, get_recommendations
from backend.games.game_service import get_game_history
from backend.library.library_service import get_reader_library
from backend.readers.reader_service import get_reader
from backend.vocabulary.vocabulary_service import get_reader_practice_vocabulary, get_reader_vocabulary
from backend.worlds.world_service import list_reader_worlds


def _story_sort_key(story: dict[str, Any]) -> datetime:
    updated_at = story.get("updated_at")
    created_at = story.get("created_at")
    if isinstance(updated_at, datetime):
        return updated_at
    if isinstance(created_at, datetime):
        return created_at
    return datetime.min


def get_reader_home_summary(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    reader = get_reader(db, account_id, reader_id)
    library = get_reader_library(db, account_id, reader_id)
    adaptive_profile = get_adaptive_profile(db, account_id, reader_id)
    recommendations = get_recommendations(db, account_id, reader_id)
    practice_words = get_reader_practice_vocabulary(db, account_id, reader_id)
    vocabulary = get_reader_vocabulary(db, account_id, reader_id)
    game_history = get_game_history(db, account_id, reader_id, limit=5)
    worlds = list_reader_worlds(db, account_id, reader_id)

    stories = sorted(library["stories"], key=_story_sort_key, reverse=True)
    continue_story = stories[0] if stories else None
    recent_game = game_history[0] if game_history else None
    recommended_word = recommendations["recommended_words"][0] if recommendations["recommended_words"] else None

    mastered_words = len([item for item in vocabulary if (item.get("mastery_level") or 0) >= 3])

    return {
        "reader": {
            "reader_id": reader.reader_id,
            "name": reader.name,
            "age": reader.age,
            "reading_level": reader.reading_level,
            "trait_focus": reader.trait_focus,
        },
        "continue_reading": continue_story,
        "library_summary": {
            "story_count": library["story_count"],
            "world_count": len(worlds),
        },
        "vocabulary_summary": {
            "tracked_words": len(vocabulary),
            "practice_words": len(practice_words),
            "mastered_words": mastered_words,
            "recommended_word": recommended_word,
        },
        "game_summary": {
            "recent_game": recent_game,
            "recommended_game_difficulty": adaptive_profile["recommended_game_difficulty"],
            "games_played_recently": len(game_history),
        },
        "reader_path": {
            "proficiency": adaptive_profile["proficiency"],
            "recommended_story_difficulty": adaptive_profile["recommended_story_difficulty"],
            "goal_message": "Goals grow here next. Keep reading, practicing words, and playing games.",
        },
    }
