import unittest
from unittest.mock import Mock, patch

from backend.parent.analytics_service import get_parent_analytics


class ParentAnalyticsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_parent_analytics_merges_goal_and_game_practice_data(self) -> None:
        learning_insights = {
            "reader_count": 1,
            "aggregate_statistics": {
                "stories_read": 8,
                "words_mastered": 30,
                "tracked_words": 42,
                "games_played": 6,
                "average_game_score": 82.5,
            },
            "readers": [
                {
                    "reader_id": 7,
                    "name": "Ari",
                    "reading_level": "developing",
                    "proficiency": "growing",
                    "stories_read": 8,
                    "words_mastered": 30,
                    "average_game_score": 82.5,
                    "strengths": ["Pattern recognition"],
                    "focus_areas": [{"category": "games", "priority": 1, "message": "Practice slower recall"}],
                    "recommendations": {
                        "recommended_story_difficulty": 2,
                        "recommended_vocabulary_difficulty": 2,
                        "recommended_game_difficulty": 2,
                    },
                }
            ],
        }
        goals = {
            "active_goal_count": 2,
            "completed_goal_count": 1,
            "readers": [
                {
                    "reader_id": 7,
                    "goals": [
                        {
                            "goal_id": 10,
                            "reader_id": 7,
                            "goal_type": "games_played",
                            "title": "Play 5 games",
                            "target_value": 5,
                            "is_active": True,
                            "created_at": None,
                            "updated_at": None,
                            "progress": {
                                "current_value": 3,
                                "target_value": 5,
                                "progress_percent": 60,
                                "status": "active",
                                "updated_at": None,
                                "completed_at": None,
                            },
                        }
                    ],
                }
            ],
        }
        aggregate_practice = {
            "sessions_total": 6,
            "sessions_this_week": 4,
            "words_practiced": 24,
            "words_correct": 18,
            "average_success_rate": 75.0,
            "practice_time_seconds": 420,
            "strongest_game_type": "build_the_word",
            "weakest_game_type": "word_match",
            "improvement_trend": "improving",
            "accuracy_by_game_type": [],
            "repeated_missed_words": [],
        }
        reader_practice = {
            "sessions_total": 4,
            "sessions_this_week": 3,
            "words_practiced": 16,
            "words_correct": 12,
            "average_success_rate": 75.0,
            "practice_time_seconds": 240,
            "strongest_game_type": "build_the_word",
            "weakest_game_type": "word_scramble",
            "improvement_trend": "steady",
            "accuracy_by_game_type": [],
            "repeated_missed_words": [{"word_text": "Lantern", "miss_count": 2}],
        }

        with patch("backend.parent.analytics_service.get_account_learning_insights", return_value=learning_insights), patch(
            "backend.parent.analytics_service.list_parent_goals_with_progress",
            return_value=goals,
        ), patch(
            "backend.parent.analytics_service.get_account_game_practice_summary",
            return_value=aggregate_practice,
        ) as aggregate_mocked, patch(
            "backend.parent.analytics_service.get_reader_game_practice_summary",
            return_value=reader_practice,
        ) as reader_mocked:
            payload = get_parent_analytics(self.db, 42)

        self.assertEqual(payload["account_id"], 42)
        self.assertEqual(payload["aggregate_game_practice"]["sessions_this_week"], 4)
        self.assertEqual(payload["readers"][0]["goals"][0]["goal_type"], "games_played")
        self.assertEqual(payload["readers"][0]["game_practice"]["strongest_game_type"], "build_the_word")
        aggregate_mocked.assert_called_once_with(self.db, 42)
        reader_mocked.assert_called_once_with(self.db, 42, 7)


if __name__ == "__main__":
    unittest.main()
