import logging
import random
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.adaptive.adaptive_engine import recommend_game_difficulty
from backend.adaptive.adaptive_repository import list_recent_game_results
from backend.games.game_generator import (
    GameGenerationError,
    build_character_memory_questions,
    build_story_comprehension_questions,
    build_vocabulary_quiz_questions,
    build_word_puzzle_questions,
)
from backend.games.game_repository import (
    get_latest_story_for_reader,
    get_reader_for_account,
    get_story_for_reader,
    insert_game_result,
    list_story_scene_payloads,
    list_characters_by_ids,
    list_global_vocabulary_words,
    list_other_character_names,
    list_other_story_event_summaries,
    list_reader_game_results,
    list_reader_practice_vocabulary,
    list_reader_story_vocabulary,
    list_story_events,
)
from backend.story_engine.story_events import capture_generated_story_events
from backend.story_engine.story_repository import load_world_context


logger = logging.getLogger(__name__)

SUPPORTED_GAME_TYPES = {
    "word_puzzle",
    "story_comprehension",
    "character_memory",
    "vocabulary_quiz",
}


class GameServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_identifier(value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise GameServiceError(error_code="invalid_identifier", status_code=400)


def _validate_game_type(game_type: Any) -> str:
    if not isinstance(game_type, str):
        raise GameServiceError(error_code="invalid_input", status_code=400)

    normalized = game_type.strip().lower()
    if normalized not in SUPPORTED_GAME_TYPES:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    return normalized


def _validate_question_count(question_count: Any) -> int:
    if question_count is None:
        return 5
    if not isinstance(question_count, int) or question_count < 1 or question_count > 10:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    return question_count


def _validate_difficulty_level(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value < 1 or value > 3:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    return value


def _validate_score(value: Any) -> int:
    if not isinstance(value, int) or value < 0 or value > 100:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    return value


def _validate_duration(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    return value


def _resolve_difficulty(db: Session, reader_id: int, requested_difficulty: int | None) -> int:
    if requested_difficulty is not None:
        return requested_difficulty
    recent_results = list_recent_game_results(db, reader_id)
    return recommend_game_difficulty(recent_results)


def _load_vocabulary_pool(
    db: Session,
    reader_id: int,
    difficulty_level: int,
    question_count: int,
) -> tuple[list, list[str]]:
    candidate_limit = max(question_count * 3, 8)
    vocabulary_items = list_reader_practice_vocabulary(
        db,
        reader_id=reader_id,
        max_difficulty=difficulty_level,
        limit=candidate_limit,
    )

    existing_word_ids = {item.word_id for item in vocabulary_items}
    if len(vocabulary_items) < question_count:
        fallback_items = list_reader_story_vocabulary(
            db,
            reader_id=reader_id,
            max_difficulty=difficulty_level,
            limit=candidate_limit,
        )
        for item in fallback_items:
            if item.word_id in existing_word_ids:
                continue
            vocabulary_items.append(item)
            existing_word_ids.add(item.word_id)

    distractor_words = list_global_vocabulary_words(
        db,
        exclude_word_ids=list(existing_word_ids),
        limit=max(question_count * 4, 12),
    )
    return vocabulary_items, distractor_words


def _resolve_story(db: Session, reader_id: int, story_id: int | None):
    if story_id is None:
        return get_latest_story_for_reader(db, reader_id)
    return get_story_for_reader(db, reader_id, story_id)


def _ensure_story_events_for_story(db: Session, story) -> list:
    story_events = list_story_events(db, story.story_id)
    if story_events:
        return story_events

    if story.world_id is None:
        return story_events

    scene_payloads = list_story_scene_payloads(db, story.story_id)
    if not scene_payloads:
        return story_events

    world_context = load_world_context(db, story.world_id)
    inserted_count = capture_generated_story_events(
        db=db,
        story_id=story.story_id,
        scenes=scene_payloads,
        world_context=world_context,
    )
    if inserted_count:
        db.commit()
    return list_story_events(db, story.story_id)


def generate_game(
    db: Session,
    account_id: int,
    reader_id: int,
    game_type: Any,
    story_id: int | None = None,
    difficulty_level: Any = None,
    question_count: Any = None,
) -> dict[str, Any]:
    _validate_identifier(reader_id)
    normalized_game_type = _validate_game_type(game_type)
    normalized_question_count = _validate_question_count(question_count)
    normalized_difficulty = _validate_difficulty_level(difficulty_level)
    if story_id is not None:
        _validate_identifier(story_id)

    logger.info(
        "game generation requested",
        extra={"reader_id": reader_id, "game_type": normalized_game_type},
    )

    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameServiceError(error_code="missing_resource", status_code=404)

        resolved_difficulty = _resolve_difficulty(db, reader_id, normalized_difficulty)
        rng = random.Random(f"{reader_id}:{normalized_game_type}:{story_id or 0}:{resolved_difficulty}")

        if normalized_game_type in {"word_puzzle", "vocabulary_quiz"}:
            vocabulary_items, distractor_words = _load_vocabulary_pool(
                db,
                reader_id=reader_id,
                difficulty_level=resolved_difficulty,
                question_count=normalized_question_count,
            )
            if normalized_game_type == "word_puzzle":
                questions = build_word_puzzle_questions(vocabulary_items, normalized_question_count, rng)
            else:
                questions = build_vocabulary_quiz_questions(
                    vocabulary_items,
                    distractor_words,
                    normalized_question_count,
                    rng,
                )
            selected_story_id = None
        else:
            story = _resolve_story(db, reader_id, story_id)
            if story is None:
                raise GameServiceError(error_code="missing_resource", status_code=404)

            story_events = _ensure_story_events_for_story(db, story)
            if not story_events:
                raise GameServiceError(error_code="missing_resource", status_code=404)

            if normalized_game_type == "story_comprehension":
                distractor_events = list_other_story_event_summaries(
                    db,
                    exclude_story_id=story.story_id,
                    limit=max(normalized_question_count * 4, 12),
                )
                questions = build_story_comprehension_questions(
                    story.title,
                    story_events,
                    distractor_events,
                    normalized_question_count,
                    rng,
                )
            else:
                character_ids: list[int] = []
                for event in story_events:
                    for character_id in event.characters:
                        if character_id not in character_ids:
                            character_ids.append(character_id)

                character_records = list_characters_by_ids(db, character_ids)
                character_name_lookup = {
                    record.character_id: record.name
                    for record in character_records
                    if record.name
                }
                distractor_names = list_other_character_names(
                    db,
                    exclude_character_ids=list(character_name_lookup.keys()),
                    limit=max(normalized_question_count * 4, 12),
                )
                questions = build_character_memory_questions(
                    story.title,
                    story_events,
                    character_name_lookup,
                    distractor_names,
                    normalized_question_count,
                    rng,
                )
            selected_story_id = story.story_id
    except GameServiceError:
        db.rollback()
        raise
    except GameGenerationError as exc:
        db.rollback()
        logger.warning(
            "game generation missing content",
            extra={"reader_id": reader_id, "game_type": normalized_game_type},
        )
        raise GameServiceError(error_code="missing_resource", status_code=404) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "database failure during game generation",
            extra={"reader_id": reader_id, "game_type": normalized_game_type},
        )
        raise GameServiceError(error_code="database_failure", status_code=500) from exc
    except HTTPException as exc:
        db.rollback()
        logger.warning(
            "upstream validation failed during game generation",
            extra={"reader_id": reader_id, "game_type": normalized_game_type},
        )
        raise GameServiceError(error_code="missing_resource", status_code=exc.status_code) from exc

    if not questions:
        raise GameServiceError(error_code="missing_resource", status_code=404)

    return {
        "reader_id": reader_id,
        "game_type": normalized_game_type,
        "story_id": selected_story_id,
        "difficulty_level": resolved_difficulty,
        "questions": questions,
    }


def record_game_result(
    db: Session,
    account_id: int,
    reader_id: int,
    game_type: Any,
    difficulty_level: Any,
    score: Any,
    duration_seconds: Any,
) -> dict[str, Any]:
    _validate_identifier(reader_id)
    normalized_game_type = _validate_game_type(game_type)
    normalized_difficulty = _validate_difficulty_level(difficulty_level)
    if normalized_difficulty is None:
        raise GameServiceError(error_code="invalid_input", status_code=400)
    normalized_score = _validate_score(score)
    normalized_duration = _validate_duration(duration_seconds)

    logger.info(
        "game result submission requested",
        extra={"reader_id": reader_id, "game_type": normalized_game_type},
    )

    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameServiceError(error_code="missing_resource", status_code=404)

        game_result_id = insert_game_result(
            db,
            reader_id=reader_id,
            game_type=normalized_game_type,
            difficulty_level=normalized_difficulty,
            score=normalized_score,
            duration_seconds=normalized_duration,
        )
        db.commit()
    except GameServiceError:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "database failure during game result submission",
            extra={"reader_id": reader_id, "game_type": normalized_game_type},
        )
        raise GameServiceError(error_code="database_failure", status_code=500) from exc

    return {
        "game_result_id": game_result_id,
        "status": "result_recorded",
    }


def get_game_history(
    db: Session,
    account_id: int,
    reader_id: int,
    limit: Any = 20,
) -> list[dict[str, Any]]:
    _validate_identifier(reader_id)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise GameServiceError(error_code="invalid_input", status_code=400)

    logger.info("game history requested", extra={"reader_id": reader_id})

    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameServiceError(error_code="missing_resource", status_code=404)

        history = list_reader_game_results(db, reader_id, limit=limit)
    except GameServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during game history lookup", extra={"reader_id": reader_id})
        raise GameServiceError(error_code="database_failure", status_code=500) from exc

    return [
        {
            "game_result_id": item.game_result_id,
            "game_type": item.game_type,
            "difficulty_level": item.difficulty_level,
            "score": item.score,
            "duration_seconds": item.duration_seconds,
            "played_at": item.played_at,
        }
        for item in history
    ]
