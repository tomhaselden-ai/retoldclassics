import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.adaptive.adaptive_engine import (
    build_story_parameters,
    compute_reader_proficiency,
    recommend_game_difficulty,
    recommend_story_difficulty,
    recommend_vocabulary_difficulty,
)
from backend.adaptive.adaptive_repository import (
    get_reader_for_account,
    get_reader_progress,
    list_reader_vocabulary_progress,
    list_recent_game_results,
)


def get_adaptive_profile(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    logging.info("Loading adaptive profile for reader %s", reader_id)
    reader = get_reader_for_account(db, account_id, reader_id)
    progress = get_reader_progress(db, reader.reader_id)
    vocabulary_progress = list_reader_vocabulary_progress(db, reader.reader_id)
    game_results = list_recent_game_results(db, reader.reader_id)

    proficiency = compute_reader_proficiency(
        progress,
        vocabulary_progress,
        game_results,
        reader.reading_level,
    )
    story_difficulty = recommend_story_difficulty(progress, reader.reading_level)
    vocabulary_difficulty = recommend_vocabulary_difficulty(vocabulary_progress)
    game_difficulty = recommend_game_difficulty(game_results)

    return {
        "reader_id": reader.reader_id,
        "reading_level": reader.reading_level,
        "stories_read": progress.stories_read,
        "words_mastered": progress.words_mastered,
        "reading_speed": progress.reading_speed,
        "proficiency": proficiency,
        "recommended_story_difficulty": story_difficulty,
        "recommended_vocabulary_difficulty": vocabulary_difficulty,
        "recommended_game_difficulty": game_difficulty,
    }


def get_recommendations(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    logging.info("Loading adaptive recommendations for reader %s", reader_id)
    reader = get_reader_for_account(db, account_id, reader_id)
    progress = get_reader_progress(db, reader.reader_id)
    vocabulary_progress = list_reader_vocabulary_progress(db, reader.reader_id)
    game_results = list_recent_game_results(db, reader.reader_id)

    story_difficulty = recommend_story_difficulty(progress, reader.reading_level)
    vocabulary_difficulty = recommend_vocabulary_difficulty(vocabulary_progress)
    game_difficulty = recommend_game_difficulty(game_results)

    recommended_words = [
        {
            "word_id": item.word_id,
            "word": item.word,
            "difficulty_level": item.difficulty_level,
            "mastery_level": item.mastery_level,
            "last_seen": item.last_seen,
        }
        for item in vocabulary_progress
        if (item.mastery_level or 0) < 2 and (item.difficulty_level or 1) <= vocabulary_difficulty
    ][:10]

    return {
        "recommended_words": recommended_words,
        "recommended_story_parameters": build_story_parameters(progress, story_difficulty),
        "recommended_game_difficulty": game_difficulty,
    }
