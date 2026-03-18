from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.games.game_repository import get_reader_for_account
from backend.games.game_session_repository import (
    GameSessionRecord,
    GameWordAttemptRecord,
    list_game_sessions_for_account,
    list_word_attempts_for_sessions,
)


class GameReportingServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _safe_rate(correct: int, attempted: int) -> float | None:
    if attempted <= 0:
        return None
    return round((correct / attempted) * 100, 1)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _compute_improvement_trend(sessions: list[GameSessionRecord]) -> str:
    scored_sessions = [session for session in sessions if session.words_attempted > 0]
    if len(scored_sessions) < 4:
        return "building"

    ordered = sorted(
        scored_sessions,
        key=lambda session: _normalize_datetime(session.ended_at)
        or _normalize_datetime(session.started_at)
        or datetime.min.replace(tzinfo=timezone.utc),
    )
    midpoint = len(ordered) // 2
    earlier = ordered[:midpoint]
    recent = ordered[midpoint:]

    if not earlier or not recent:
        return "building"

    earlier_rate = sum((session.words_correct / session.words_attempted) for session in earlier) / len(earlier)
    recent_rate = sum((session.words_correct / session.words_attempted) for session in recent) / len(recent)
    delta = recent_rate - earlier_rate

    if delta >= 0.08:
        return "improving"
    if delta <= -0.08:
        return "needs_support"
    return "steady"


def _build_practice_summary(
    *,
    sessions: list[GameSessionRecord],
    attempts: list[GameWordAttemptRecord],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    sessions_total = len(sessions)
    sessions_this_week = 0
    words_practiced = 0
    words_correct = 0
    practice_time_seconds = 0

    by_game_type: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "game_type": None,
            "sessions_played": 0,
            "words_attempted": 0,
            "words_correct": 0,
        }
    )
    missed_word_counts: dict[str, dict[str, Any]] = {}

    for session in sessions:
        session_timestamp = _normalize_datetime(session.ended_at) or _normalize_datetime(session.started_at)
        if session_timestamp and session_timestamp >= week_ago:
            sessions_this_week += 1

        words_practiced += session.words_attempted
        words_correct += session.words_correct
        practice_time_seconds += session.duration_seconds or 0

        game_summary = by_game_type[session.game_type]
        game_summary["game_type"] = session.game_type
        game_summary["sessions_played"] += 1
        game_summary["words_attempted"] += session.words_attempted
        game_summary["words_correct"] += session.words_correct

    for attempt in attempts:
        if attempt.correct or attempt.skipped:
            continue
        normalized_word = attempt.word_text.strip().lower()
        if not normalized_word:
            continue
        bucket = missed_word_counts.setdefault(
            normalized_word,
            {
                "word_text": attempt.word_text.strip(),
                "miss_count": 0,
            },
        )
        bucket["miss_count"] += 1

    accuracy_by_game_type = []
    for game_type, values in sorted(by_game_type.items(), key=lambda item: item[0]):
        accuracy_by_game_type.append(
            {
                "game_type": game_type,
                "sessions_played": values["sessions_played"],
                "words_attempted": values["words_attempted"],
                "words_correct": values["words_correct"],
                "success_rate": _safe_rate(values["words_correct"], values["words_attempted"]),
            }
        )

    scored_game_types = [entry for entry in accuracy_by_game_type if entry["success_rate"] is not None]
    strongest_game_type = None
    weakest_game_type = None
    if scored_game_types:
        strongest_game_type = max(
            scored_game_types,
            key=lambda entry: (entry["success_rate"], entry["words_attempted"]),
        )["game_type"]
        weakest_game_type = min(
            scored_game_types,
            key=lambda entry: (entry["success_rate"], -entry["words_attempted"]),
        )["game_type"]

    repeated_missed_words = sorted(
        missed_word_counts.values(),
        key=lambda item: (-item["miss_count"], item["word_text"].lower()),
    )[:5]

    return {
        "sessions_total": sessions_total,
        "sessions_this_week": sessions_this_week,
        "words_practiced": words_practiced,
        "words_correct": words_correct,
        "average_success_rate": _safe_rate(words_correct, words_practiced),
        "practice_time_seconds": practice_time_seconds,
        "strongest_game_type": strongest_game_type,
        "weakest_game_type": weakest_game_type,
        "improvement_trend": _compute_improvement_trend(sessions),
        "accuracy_by_game_type": accuracy_by_game_type,
        "repeated_missed_words": repeated_missed_words,
    }


def _load_summary(
    db: Session,
    *,
    account_id: int,
    reader_id: int | None = None,
) -> dict[str, Any]:
    sessions = list_game_sessions_for_account(
        db,
        account_id=account_id,
        reader_id=reader_id,
        completion_status="completed",
    )
    attempts = list_word_attempts_for_sessions(db, session_ids=[session.session_id for session in sessions])
    return _build_practice_summary(sessions=sessions, attempts=attempts)


def get_reader_game_practice_summary(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    try:
        reader = get_reader_for_account(db, reader_id, account_id)
        if reader is None:
            raise GameReportingServiceError("missing_resource", 404)
        return _load_summary(db, account_id=account_id, reader_id=reader_id)
    except GameReportingServiceError:
        raise
    except SQLAlchemyError as exc:
        raise GameReportingServiceError("database_failure", 500) from exc


def get_account_game_practice_summary(db: Session, account_id: int) -> dict[str, Any]:
    try:
        return _load_summary(db, account_id=account_id)
    except SQLAlchemyError as exc:
        raise GameReportingServiceError("database_failure", 500) from exc
