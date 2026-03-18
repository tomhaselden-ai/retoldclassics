import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.goals.goal_service import create_reader_goal, list_parent_goals_with_progress, list_reader_goals_with_progress


class GoalServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_create_reader_goal_builds_default_title_and_progress(self) -> None:
        goal_record = Mock()
        goal_record.goal_id = 17
        goal_record.reader_id = 7
        goal_record.goal_type = "stories_read"
        goal_record.title = "Read stories: 4"
        goal_record.target_value = 4
        goal_record.is_active = True
        goal_record.created_at = datetime(2026, 3, 17)
        goal_record.updated_at = datetime(2026, 3, 17)

        progress_record = Mock()
        progress_record.current_value = 3
        progress_record.target_value = 4
        progress_record.progress_percent = 75
        progress_record.status = "active"
        progress_record.updated_at = datetime(2026, 3, 17)
        progress_record.completed_at = None

        with patch("backend.goals.goal_service.get_reader"), patch(
            "backend.goals.goal_service.insert_goal",
            return_value=17,
        ) as insert_mocked, patch(
            "backend.goals.goal_service.get_goal_for_account",
            return_value=goal_record,
        ), patch(
            "backend.goals.goal_service.get_reader_learning_insights",
            return_value={
                "reading_summary": {"stories_read": 3, "words_mastered": 0},
                "game_summary": {"total_games_played": 0},
                "vocabulary_summary": {"tracked_words": 0},
            },
        ), patch("backend.goals.goal_service.upsert_goal_progress") as upsert_mocked, patch(
            "backend.goals.goal_service.get_progress_for_goal",
            side_effect=[None, progress_record],
        ):
            payload = create_reader_goal(self.db, 42, 7, "stories_read", 4)

        insert_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=7,
            goal_type="stories_read",
            title="Read stories: 4",
            target_value=4,
        )
        upsert_mocked.assert_called_once()
        self.assertEqual(payload["goal_id"], 17)
        self.assertEqual(payload["progress"]["progress_percent"], 75)

    def test_list_parent_goals_groups_progress_by_reader(self) -> None:
        goal_one = Mock()
        goal_one.goal_id = 1
        goal_one.reader_id = 7
        goal_one.goal_type = "stories_read"
        goal_one.title = "Read 5 stories"
        goal_one.target_value = 5
        goal_one.is_active = True
        goal_one.created_at = None
        goal_one.updated_at = None

        goal_two = Mock()
        goal_two.goal_id = 2
        goal_two.reader_id = 8
        goal_two.goal_type = "words_mastered"
        goal_two.title = "Master 10 words"
        goal_two.target_value = 10
        goal_two.is_active = True
        goal_two.created_at = None
        goal_two.updated_at = None

        with patch(
            "backend.goals.goal_service.get_account_learning_insights",
            return_value={
                "readers": [
                    {"reader_id": 7, "name": "Ari", "reading_level": "developing", "proficiency": "growing"},
                    {"reader_id": 8, "name": "Lum", "reading_level": "confident", "proficiency": "confident"},
                ]
            },
        ), patch(
            "backend.goals.goal_service.list_goals_for_account",
            return_value=[goal_one, goal_two],
        ), patch(
            "backend.goals.goal_service._sync_goal_progress",
            side_effect=[
                {
                    "goal_id": 1,
                    "reader_id": 7,
                    "goal_type": "stories_read",
                    "title": "Read 5 stories",
                    "target_value": 5,
                    "is_active": True,
                    "created_at": None,
                    "updated_at": None,
                    "progress": {"status": "active", "progress_percent": 60},
                },
                {
                    "goal_id": 2,
                    "reader_id": 8,
                    "goal_type": "words_mastered",
                    "title": "Master 10 words",
                    "target_value": 10,
                    "is_active": True,
                    "created_at": None,
                    "updated_at": None,
                    "progress": {"status": "completed", "progress_percent": 100},
                },
            ],
        ):
            payload = list_parent_goals_with_progress(self.db, 42)

        self.assertEqual(payload["account_id"], 42)
        self.assertEqual(payload["active_goal_count"], 2)
        self.assertEqual(payload["completed_goal_count"], 1)
        self.assertEqual(payload["readers"][0]["goals"][0]["goal_id"], 1)
        self.assertEqual(payload["readers"][1]["goals"][0]["goal_id"], 2)

    def test_list_reader_goals_returns_reader_summary_and_goals(self) -> None:
        reader_record = Mock()
        reader_record.reader_id = 7
        reader_record.name = "Ari"
        reader_record.reading_level = "developing"

        goal = Mock()
        goal.goal_id = 1
        goal.reader_id = 7

        with patch("backend.goals.goal_service.get_reader", return_value=reader_record), patch(
            "backend.goals.goal_service.list_goals_for_reader",
            return_value=[goal],
        ), patch(
            "backend.goals.goal_service._sync_goal_progress",
            return_value={
                "goal_id": 1,
                "reader_id": 7,
                "goal_type": "stories_read",
                "title": "Read 5 stories",
                "target_value": 5,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
                "progress": {"status": "active", "progress_percent": 80},
            },
        ):
            payload = list_reader_goals_with_progress(self.db, 42, 7)

        self.assertEqual(payload["reader"]["name"], "Ari")
        self.assertEqual(payload["goals"][0]["progress"]["progress_percent"], 80)


if __name__ == "__main__":
    unittest.main()
