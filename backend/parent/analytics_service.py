from typing import Any

from sqlalchemy.orm import Session

from backend.analytics.analytics_service import AnalyticsServiceError, get_account_learning_insights
from backend.games.game_reporting_service import (
    GameReportingServiceError,
    get_account_game_practice_summary,
    get_reader_game_practice_summary,
)
from backend.goals.goal_service import GoalServiceError, list_parent_goals_with_progress


class ParentAnalyticsServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def get_parent_analytics(db: Session, account_id: int) -> dict[str, Any]:
    try:
        learning_insights = get_account_learning_insights(db, account_id, account_id)
        goal_summary = list_parent_goals_with_progress(db, account_id)
        aggregate_game_practice = get_account_game_practice_summary(db, account_id)
    except AnalyticsServiceError as exc:
        raise ParentAnalyticsServiceError(exc.error_code, exc.status_code) from exc
    except GoalServiceError as exc:
        raise ParentAnalyticsServiceError(exc.error_code, exc.status_code) from exc
    except GameReportingServiceError as exc:
        raise ParentAnalyticsServiceError(exc.error_code, exc.status_code) from exc

    readers = []
    goals_by_reader = {reader["reader_id"]: reader["goals"] for reader in goal_summary["readers"]}
    for reader in learning_insights["readers"]:
        reader_id = reader["reader_id"]
        readers.append(
            {
                **reader,
                "goals": goals_by_reader.get(reader_id, []),
                "game_practice": get_reader_game_practice_summary(db, account_id, reader_id),
            }
        )

    return {
        "account_id": account_id,
        "reader_count": learning_insights["reader_count"],
        "aggregate_statistics": learning_insights["aggregate_statistics"],
        "aggregate_game_practice": aggregate_game_practice,
        "goal_summary": {
            "active_goal_count": goal_summary["active_goal_count"],
            "completed_goal_count": goal_summary["completed_goal_count"],
        },
        "readers": readers,
    }
