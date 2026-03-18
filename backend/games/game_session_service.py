from __future__ import annotations

from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.adaptive.adaptive_engine import recommend_game_difficulty
from backend.adaptive.adaptive_repository import list_recent_game_results
from backend.games.v1_game_engine import build_v1_game_payload
from backend.games.game_repository import (
    get_latest_story_for_reader,
    get_reader_for_account,
    get_story_for_reader,
    insert_game_result,
)
from backend.games.game_session_repository import (
    create_game_session,
    get_game_session_for_account,
    list_global_word_items,
    list_reader_practice_word_items,
    list_reader_story_word_items,
    list_recent_game_sessions_for_reader,
    list_word_attempts_for_session,
    replace_word_attempts,
    update_game_session_completion,
)


SUPPORTED_V1_GAME_TYPES = {
    "build_the_word",
    "guess_the_word",
    "word_match",
    "word_scramble",
    "flash_cards",
    "crossword",
}

SUPPORTED_SOURCE_TYPES = {
    "story",
    "global_vocab",
}


class GameSessionServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_identifier(value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise GameSessionServiceError("invalid_identifier", 400)


def _validate_game_type(game_type: Any) -> str:
    if not isinstance(game_type, str):
        raise GameSessionServiceError("invalid_input", 400)
    normalized = game_type.strip().lower()
    if normalized not in SUPPORTED_V1_GAME_TYPES:
        raise GameSessionServiceError("invalid_input", 400)
    return normalized


def _validate_source_type(source_type: Any) -> str | None:
    if source_type is None:
        return None
    if not isinstance(source_type, str):
        raise GameSessionServiceError("invalid_input", 400)
    normalized = source_type.strip().lower()
    if normalized not in SUPPORTED_SOURCE_TYPES:
        raise GameSessionServiceError("invalid_input", 400)
    return normalized


def _validate_difficulty_level(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value < 1 or value > 3:
        raise GameSessionServiceError("invalid_input", 400)
    return value


def _validate_item_count(value: Any) -> int:
    if value is None:
        return 8
    if not isinstance(value, int) or value < 4 or value > 16:
        raise GameSessionServiceError("invalid_input", 400)
    return value


def _summarize_recent_results(recent_results: list[Any]) -> dict[str, Any]:
    if not recent_results:
        return {"average_score": None, "session_count": 0}
    average_score = sum((item.score or 0) for item in recent_results) / len(recent_results)
    return {"average_score": average_score, "session_count": len(recent_results)}


def _resolve_hint_mode(game_type: str, recent_results: list[Any]) -> str:
    snapshot = _summarize_recent_results(recent_results)
    average_score = snapshot["average_score"]
    if game_type == "crossword":
        if average_score is None or average_score < 70:
            return "guided"
        if average_score < 85:
            return "balanced"
        return "light"
    if average_score is None or average_score < 60:
        return "supportive"
    if average_score < 85:
        return "balanced"
    return "light"


def _resolve_item_count(game_type: str, difficulty_level: int, requested_item_count: int | None) -> int:
    if requested_item_count is not None:
        return requested_item_count
    if game_type == "crossword":
        return 4 if difficulty_level == 1 else 5 if difficulty_level == 2 else 6
    return 6 if difficulty_level == 1 else 8 if difficulty_level == 2 else 10


def _resolve_source_selection(
    db: Session,
    *,
    reader_id: int,
    requested_source_type: str | None,
    requested_story_id: int | None,
) -> tuple[str, int | None, str]:
    if requested_story_id is not None:
        return "story", requested_story_id, "specific_story"

    latest_story = get_latest_story_for_reader(db, reader_id)
    if requested_source_type == "global_vocab":
        return "global_vocab", None, "reader_vocabulary"
    if requested_source_type == "story":
        return ("story", latest_story.story_id if latest_story else None, "recent_story" if latest_story else "story_words")
    if latest_story is not None:
        return "story", latest_story.story_id, "recent_story"
    return "global_vocab", None, "reader_vocabulary"


def _resolve_difficulty(db: Session, reader_id: int, requested_difficulty: int | None) -> int:
    if requested_difficulty is not None:
        return requested_difficulty
    recent_results = list_recent_game_results(db, reader_id)
    return recommend_game_difficulty(recent_results)


def _unique_word_items(items: list[Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for item in items:
        if not item.word:
            continue
        normalized = item.word.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "word_id": item.word_id,
                "word": normalized,
                "definition": item.definition,
                "example_sentence": item.example_sentence,
                "difficulty_level": item.difficulty_level,
                "reader_id": item.reader_id,
                "story_id": item.story_id,
                "source_type": item.source_type,
                "trait_focus": item.trait_focus,
            }
        )
    return results


def _load_session_items(
    db: Session,
    *,
    reader_id: int,
    difficulty_level: int,
    item_count: int,
    source_type: str,
    story_id: int | None,
) -> list[dict[str, Any]]:
    items: list[Any] = []

    if source_type == "story":
        if story_id is not None:
            items.extend(
                list_reader_story_word_items(
                    db,
                    reader_id=reader_id,
                    max_difficulty=difficulty_level,
                    limit=item_count * 2,
                    story_id=story_id,
                )
            )
        items.extend(
            list_reader_practice_word_items(
                db,
                reader_id=reader_id,
                max_difficulty=difficulty_level,
                limit=item_count * 2,
            )
        )
        items.extend(
            list_reader_story_word_items(
                db,
                reader_id=reader_id,
                max_difficulty=difficulty_level,
                limit=item_count * 2,
            )
        )
    else:
        items.extend(
            list_global_word_items(
                db,
                reader_id=reader_id,
                max_difficulty=difficulty_level,
                limit=item_count * 3,
                exclude_word_ids=[],
            )
        )

    unique_items = _unique_word_items(items)

    if source_type != "global_vocab" and len(unique_items) < item_count:
        exclude_ids = [item["word_id"] for item in unique_items if isinstance(item.get("word_id"), int)]
        unique_items.extend(
            _unique_word_items(
                list_global_word_items(
                    db,
                    reader_id=reader_id,
                    max_difficulty=difficulty_level,
                    limit=item_count * 2,
                    exclude_word_ids=exclude_ids,
                )
            )
        )
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in unique_items:
            key = item["word"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        unique_items = deduped

    return unique_items[:item_count]


def _extract_payload_items(session_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(session_payload, dict):
        return []
    items = session_payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and isinstance(item.get("word"), str)]


def get_game_catalog(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    _validate_identifier(reader_id)

    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameSessionServiceError("missing_resource", 404)

        recommended_difficulty = recommend_game_difficulty(list_recent_game_results(db, reader_id))
        recent_sessions = list_recent_game_sessions_for_reader(db, account_id=account_id, reader_id=reader_id, limit=5)
    except GameSessionServiceError:
        raise
    except SQLAlchemyError as exc:
        raise GameSessionServiceError("database_failure", 500) from exc

    return {
        "reader_id": reader_id,
        "recommended_difficulty": recommended_difficulty,
        "games": [
            {
                "game_type": "build_the_word",
                "label": "Build the Word",
                "description": "Guess letters to reveal a hidden word.",
                "default_item_count": 8,
                "supports_story_source": True,
            },
            {
                "game_type": "guess_the_word",
                "label": "Guess the Word",
                "description": "Use the clue and fill in the missing word.",
                "default_item_count": 8,
                "supports_story_source": True,
            },
            {
                "game_type": "word_match",
                "label": "Word Match",
                "description": "Match each word to its meaning.",
                "default_item_count": 8,
                "supports_story_source": True,
            },
            {
                "game_type": "word_scramble",
                "label": "Word Scramble",
                "description": "Reorder scrambled letters into the right word.",
                "default_item_count": 8,
                "supports_story_source": True,
            },
            {
                "game_type": "flash_cards",
                "label": "Flash Cards",
                "description": "Review words and reveal their meanings.",
                "default_item_count": 8,
                "supports_story_source": True,
            },
            {
                "game_type": "crossword",
                "label": "Crossword",
                "description": "Fill a connected word grid using clues from reading practice.",
                "default_item_count": 5,
                "supports_story_source": True,
            },
        ],
        "recent_sessions": [
            {
                "session_id": session.session_id,
                "game_type": session.game_type,
                "completion_status": session.completion_status,
                "duration_seconds": session.duration_seconds,
                "started_at": session.started_at,
                "ended_at": session.ended_at,
            }
            for session in recent_sessions
        ],
    }


def create_v1_game_session(
    db: Session,
    account_id: int,
    reader_id: int,
    *,
    game_type: Any,
    story_id: int | None = None,
    source_type: Any = None,
    difficulty_level: Any = None,
    item_count: Any = None,
) -> dict[str, Any]:
    _validate_identifier(reader_id)
    normalized_game_type = _validate_game_type(game_type)
    normalized_source_type = _validate_source_type(source_type)
    normalized_difficulty = _validate_difficulty_level(difficulty_level)
    normalized_item_count = _validate_item_count(item_count) if item_count is not None else None
    if story_id is not None:
        _validate_identifier(story_id)

    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameSessionServiceError("missing_resource", 404)

        if story_id is not None and get_story_for_reader(db, reader_id, story_id) is None:
            raise GameSessionServiceError("missing_resource", 404)

        recent_results = list_recent_game_results(db, reader_id)
        resolved_difficulty = normalized_difficulty if normalized_difficulty is not None else recommend_game_difficulty(recent_results)
        resolved_source_type, resolved_story_id, source_reason = _resolve_source_selection(
            db,
            reader_id=reader_id,
            requested_source_type=normalized_source_type,
            requested_story_id=story_id,
        )
        resolved_item_count = _resolve_item_count(normalized_game_type, resolved_difficulty, normalized_item_count)
        launch_config = {
            "launch_mode": "auto" if normalized_source_type is None and normalized_difficulty is None and normalized_item_count is None and story_id is None else "custom",
            "hint_mode": _resolve_hint_mode(normalized_game_type, recent_results),
            "session_size": resolved_item_count,
            "source_reason": source_reason,
            "auto_selected_story": resolved_story_id,
        }
        items = _load_session_items(
            db,
            reader_id=reader_id,
            difficulty_level=resolved_difficulty,
            item_count=resolved_item_count,
            source_type=resolved_source_type,
            story_id=resolved_story_id,
        )
        if len(items) < 4:
            raise GameSessionServiceError("missing_resource", 404)
        session_payload = build_v1_game_payload(
            game_type=normalized_game_type,
            difficulty_level=resolved_difficulty,
            items=items,
            launch_config=launch_config,
        )

        session_id = create_game_session(
            db,
            account_id=account_id,
            reader_id=reader_id,
            game_type=normalized_game_type,
            source_type=resolved_source_type,
            source_story_id=resolved_story_id,
            difficulty_level=resolved_difficulty,
            item_count=len(items),
            session_payload=session_payload,
        )
        session = get_game_session_for_account(db, account_id=account_id, reader_id=reader_id, session_id=session_id)
        db.commit()
    except GameSessionServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise GameSessionServiceError("database_failure", 500) from exc

    if session is None:
        raise GameSessionServiceError("missing_resource", 404)

    return {
        "session_id": session.session_id,
        "reader_id": session.reader_id,
        "game_type": session.game_type,
        "source_type": session.source_type,
        "source_story_id": session.source_story_id,
        "difficulty_level": session.difficulty_level,
        "status": session.status,
        "completion_status": session.completion_status,
        "started_at": session.started_at,
        "items": items,
        "payload": session_payload,
    }


def get_v1_game_session(db: Session, account_id: int, reader_id: int, session_id: int) -> dict[str, Any]:
    _validate_identifier(reader_id)
    _validate_identifier(session_id)

    try:
        session = get_game_session_for_account(db, account_id=account_id, reader_id=reader_id, session_id=session_id)
        if session is None:
            raise GameSessionServiceError("missing_resource", 404)
        attempts = list_word_attempts_for_session(db, session_id=session_id)
    except GameSessionServiceError:
        raise
    except SQLAlchemyError as exc:
        raise GameSessionServiceError("database_failure", 500) from exc

    return {
        "session_id": session.session_id,
        "reader_id": session.reader_id,
        "game_type": session.game_type,
        "source_type": session.source_type,
        "source_story_id": session.source_story_id,
        "difficulty_level": session.difficulty_level,
        "status": session.status,
        "item_count": session.item_count,
        "words_attempted": session.words_attempted,
        "words_correct": session.words_correct,
        "words_incorrect": session.words_incorrect,
        "hints_used": session.hints_used,
        "completion_status": session.completion_status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_seconds": session.duration_seconds,
        "items": _extract_payload_items(session.session_payload),
        "payload": session.session_payload,
        "attempts": [
            {
                "attempt_id": attempt.attempt_id,
                "word_id": attempt.word_id,
                "word_text": attempt.word_text,
                "game_type": attempt.game_type,
                "attempt_count": attempt.attempt_count,
                "correct": attempt.correct,
                "time_spent_seconds": attempt.time_spent_seconds,
                "hint_used": attempt.hint_used,
                "skipped": attempt.skipped,
                "created_at": attempt.created_at,
            }
            for attempt in attempts
        ],
    }


def complete_v1_game_session(
    db: Session,
    account_id: int,
    reader_id: int,
    session_id: int,
    *,
    completion_status: Any,
    duration_seconds: Any,
    attempts: Any,
) -> dict[str, Any]:
    _validate_identifier(reader_id)
    _validate_identifier(session_id)
    if not isinstance(duration_seconds, int) or duration_seconds <= 0:
        raise GameSessionServiceError("invalid_input", 400)
    if not isinstance(completion_status, str) or completion_status.strip().lower() not in {"completed", "abandoned"}:
        raise GameSessionServiceError("invalid_input", 400)
    if not isinstance(attempts, list) or not attempts:
        raise GameSessionServiceError("invalid_input", 400)

    normalized_completion_status = completion_status.strip().lower()
    normalized_attempts: list[dict[str, Any]] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            raise GameSessionServiceError("invalid_input", 400)
        word_text = attempt.get("word_text")
        attempt_count = attempt.get("attempt_count")
        time_spent_seconds = attempt.get("time_spent_seconds")
        if not isinstance(word_text, str) or not word_text.strip():
            raise GameSessionServiceError("invalid_input", 400)
        if not isinstance(attempt_count, int) or attempt_count < 0:
            raise GameSessionServiceError("invalid_input", 400)
        if not isinstance(time_spent_seconds, int) or time_spent_seconds < 0:
            raise GameSessionServiceError("invalid_input", 400)

        normalized_attempts.append(
            {
                "word_id": attempt.get("word_id") if isinstance(attempt.get("word_id"), int) else None,
                "word_text": word_text.strip(),
                "attempt_count": attempt_count,
                "correct": bool(attempt.get("correct")),
                "time_spent_seconds": time_spent_seconds,
                "hint_used": bool(attempt.get("hint_used")),
                "skipped": bool(attempt.get("skipped")),
            }
        )

    try:
        session = get_game_session_for_account(db, account_id=account_id, reader_id=reader_id, session_id=session_id)
        if session is None:
            raise GameSessionServiceError("missing_resource", 404)
        if session.status == "completed":
            raise GameSessionServiceError("invalid_input", 400)

        words_attempted = len(normalized_attempts)
        words_correct = sum(1 for attempt in normalized_attempts if attempt["correct"])
        words_incorrect = sum(1 for attempt in normalized_attempts if not attempt["correct"] and not attempt["skipped"])
        hints_used = sum(1 for attempt in normalized_attempts if attempt["hint_used"])

        replace_word_attempts(
            db,
            session_id=session_id,
            game_type=session.game_type,
            attempts=normalized_attempts,
        )
        update_game_session_completion(
            db,
            session_id=session_id,
            words_attempted=words_attempted,
            words_correct=words_correct,
            words_incorrect=words_incorrect,
            hints_used=hints_used,
            completion_status=normalized_completion_status,
            duration_seconds=duration_seconds,
        )
        score = 0 if words_attempted == 0 else round((words_correct / words_attempted) * 100)
        game_result_id = insert_game_result(
            db,
            reader_id=reader_id,
            game_type=session.game_type,
            difficulty_level=session.difficulty_level,
            score=score,
            duration_seconds=duration_seconds,
        )
        db.commit()
        updated_session = get_game_session_for_account(db, account_id=account_id, reader_id=reader_id, session_id=session_id)
    except GameSessionServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise GameSessionServiceError("database_failure", 500) from exc

    if updated_session is None:
        raise GameSessionServiceError("missing_resource", 404)

    return {
        "session_id": updated_session.session_id,
        "reader_id": updated_session.reader_id,
        "game_type": updated_session.game_type,
        "difficulty_level": updated_session.difficulty_level,
        "status": updated_session.status,
        "completion_status": updated_session.completion_status,
        "words_attempted": updated_session.words_attempted,
        "words_correct": updated_session.words_correct,
        "words_incorrect": updated_session.words_incorrect,
        "hints_used": updated_session.hints_used,
        "duration_seconds": updated_session.duration_seconds,
        "legacy_game_result_id": game_result_id,
    }
