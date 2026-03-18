from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.analytics.analytics_service import get_account_learning_insights, get_reader_learning_insights
from backend.goals.goal_repository import (
    get_goal_for_account,
    get_progress_for_goal,
    insert_goal,
    list_goals_for_account,
    list_goals_for_reader,
    update_goal_record,
    upsert_goal_progress,
)
from backend.readers.reader_service import get_reader


SUPPORTED_GOAL_TYPES = {
    "stories_read": "Read stories",
    "words_mastered": "Master words",
    "games_played": "Play games",
    "tracked_words": "Learn new words",
}


class GoalServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_goal_type(value: Any) -> str:
    if not isinstance(value, str):
        raise GoalServiceError("invalid_input", 400)
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_GOAL_TYPES:
        raise GoalServiceError("invalid_input", 400)
    return normalized


def _validate_target_value(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        raise GoalServiceError("invalid_input", 400)
    return value


def _build_goal_title(goal_type: str, target_value: int, title: Any) -> str:
    if isinstance(title, str) and title.strip():
        return title.strip()[:255]
    return f"{SUPPORTED_GOAL_TYPES[goal_type]}: {target_value}"


def _metric_value_for_goal(goal_type: str, reader_insights: dict[str, Any]) -> int:
    if goal_type == "stories_read":
        return int(reader_insights["reading_summary"]["stories_read"])
    if goal_type == "words_mastered":
        return int(reader_insights["reading_summary"]["words_mastered"])
    if goal_type == "games_played":
        return int(reader_insights["game_summary"]["total_games_played"])
    if goal_type == "tracked_words":
        return int(reader_insights["vocabulary_summary"]["tracked_words"])
    raise GoalServiceError("invalid_input", 400)


def _serialize_goal(goal, progress) -> dict[str, Any]:
    return {
        "goal_id": goal.goal_id,
        "reader_id": goal.reader_id,
        "goal_type": goal.goal_type,
        "title": goal.title,
        "target_value": goal.target_value,
        "is_active": goal.is_active,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress": {
            "current_value": progress.current_value,
            "target_value": progress.target_value,
            "progress_percent": progress.progress_percent,
            "status": progress.status,
            "updated_at": progress.updated_at,
            "completed_at": progress.completed_at,
        },
    }


def _sync_goal_progress(db: Session, account_id: int, goal) -> dict[str, Any]:
    reader_insights = get_reader_learning_insights(db, account_id, goal.reader_id)
    current_value = _metric_value_for_goal(goal.goal_type, reader_insights)
    progress_percent = min(100, int((current_value / goal.target_value) * 100)) if goal.target_value > 0 else 0
    status = "completed" if current_value >= goal.target_value else "active"

    existing = get_progress_for_goal(db, goal.goal_id)
    completed_at = existing.completed_at if existing and existing.completed_at else None
    if status == "completed" and completed_at is None:
        completed_at = datetime.now(timezone.utc)
    if status != "completed":
        completed_at = None

    upsert_goal_progress(
        db,
        goal_id=goal.goal_id,
        reader_id=goal.reader_id,
        current_value=current_value,
        target_value=goal.target_value,
        progress_percent=progress_percent,
        status=status,
        completed_at=completed_at,
    )
    db.commit()
    progress = get_progress_for_goal(db, goal.goal_id)
    return _serialize_goal(goal, progress)


def create_reader_goal(
    db: Session,
    account_id: int,
    reader_id: int,
    goal_type: Any,
    target_value: Any,
    title: Any = None,
) -> dict[str, Any]:
    normalized_goal_type = _validate_goal_type(goal_type)
    normalized_target = _validate_target_value(target_value)
    get_reader(db, account_id, reader_id)
    goal_id = insert_goal(
        db,
        account_id=account_id,
        reader_id=reader_id,
        goal_type=normalized_goal_type,
        title=_build_goal_title(normalized_goal_type, normalized_target, title),
        target_value=normalized_target,
    )
    db.commit()
    goal = get_goal_for_account(db, account_id, goal_id)
    return _sync_goal_progress(db, account_id, goal)


def update_reader_goal(
    db: Session,
    account_id: int,
    goal_id: int,
    *,
    title: Any,
    target_value: Any,
    is_active: Any,
) -> dict[str, Any]:
    goal = get_goal_for_account(db, account_id, goal_id)
    if goal is None:
        raise GoalServiceError("missing_resource", 404)

    normalized_target = _validate_target_value(target_value)
    active_flag = bool(is_active)
    update_goal_record(
        db,
        goal_id,
        title=_build_goal_title(goal.goal_type, normalized_target, title),
        target_value=normalized_target,
        is_active=active_flag,
    )
    db.commit()
    updated_goal = get_goal_for_account(db, account_id, goal_id)
    return _sync_goal_progress(db, account_id, updated_goal)


def list_reader_goals_with_progress(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    reader = get_reader(db, account_id, reader_id)
    goals = list_goals_for_reader(db, account_id, reader_id)
    goal_payload = [_sync_goal_progress(db, account_id, goal) for goal in goals]
    return {
        "reader": {
            "reader_id": reader.reader_id,
            "name": reader.name,
            "reading_level": reader.reading_level,
        },
        "goals": goal_payload,
    }


def list_parent_goals_with_progress(db: Session, account_id: int) -> dict[str, Any]:
    account_insights = get_account_learning_insights(db, account_id, account_id)
    goals = list_goals_for_account(db, account_id)
    goals_with_progress = [_sync_goal_progress(db, account_id, goal) for goal in goals]

    grouped: dict[int, list[dict[str, Any]]] = {}
    for goal in goals_with_progress:
        grouped.setdefault(goal["reader_id"], []).append(goal)

    readers = []
    for reader in account_insights["readers"]:
        reader_goals = grouped.get(reader["reader_id"], [])
        readers.append(
            {
                "reader_id": reader["reader_id"],
                "name": reader["name"],
                "reading_level": reader["reading_level"],
                "proficiency": reader["proficiency"],
                "goals": reader_goals,
            }
        )

    active_goals = [goal for goal in goals_with_progress if goal["is_active"]]
    completed_goals = [goal for goal in goals_with_progress if goal["progress"]["status"] == "completed"]

    return {
        "account_id": account_id,
        "active_goal_count": len(active_goals),
        "completed_goal_count": len(completed_goals),
        "readers": readers,
    }
