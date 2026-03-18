import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.dashboard.dashboard_repository import (
    get_account,
    get_account_reader,
    list_account_readers,
    list_reader_game_results,
    list_reader_stories,
)
from backend.dashboard.progress_repository import get_reader_progress
from backend.vocabulary.progress_repository import list_reader_vocabulary


def _build_reader_dashboard(db: Session, reader) -> dict[str, Any]:
    progress = get_reader_progress(db, reader.reader_id)
    vocabulary_progress = list_reader_vocabulary(db, reader.reader_id)
    recent_stories = list_reader_stories(db, reader.reader_id)
    game_results = list_reader_game_results(db, reader.reader_id)

    return {
        "reader_id": reader.reader_id,
        "name": reader.name,
        "age": reader.age,
        "reading_level": reader.reading_level,
        "trait_focus": reader.trait_focus,
        "reading_statistics": {
            "stories_read": progress.stories_read,
            "words_mastered": progress.words_mastered,
            "reading_speed": progress.reading_speed,
            "preferred_themes": progress.preferred_themes,
            "traits_reinforced": progress.traits_reinforced,
        },
        "recent_stories": [
            {
                "story_id": story.story_id,
                "title": story.title,
                "created_at": story.created_at,
            }
            for story in recent_stories
        ],
        "vocabulary_progress": [
            {
                "word": item["word"],
                "difficulty_level": item["difficulty_level"],
                "mastery_level": item["mastery_level"],
                "last_seen": item["last_seen"],
            }
            for item in vocabulary_progress
        ],
        "game_results": [
            {
                "game_type": game.game_type,
                "difficulty_level": game.difficulty_level,
                "score": game.score,
                "duration_seconds": game.duration_seconds,
                "played_at": game.played_at,
            }
            for game in game_results
        ],
    }


def get_account_dashboard(db: Session, account_id: int) -> dict[str, Any]:
    logging.info("Loading dashboard for account %s", account_id)
    get_account(account_id, db)
    readers = list_account_readers(db, account_id)
    return {
        "account_id": account_id,
        "readers": [_build_reader_dashboard(db, reader) for reader in readers],
    }


def get_reader_dashboard(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    logging.info("Loading dashboard for reader %s", reader_id)
    reader = get_account_reader(db, account_id, reader_id)
    return _build_reader_dashboard(db, reader)
