import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.reader_home.home_service import get_reader_home_summary


class ReaderHomeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_get_reader_home_summary_shapes_continue_reading_and_counts(self) -> None:
        reader = Mock()
        reader.reader_id = 7
        reader.name = "Ari"
        reader.age = 8
        reader.reading_level = "developing"
        reader.trait_focus = ["curiosity"]

        library = {
            "story_count": 2,
            "stories": [
                {
                    "story_id": 10,
                    "title": "Earlier Story",
                    "updated_at": datetime(2026, 3, 1),
                    "created_at": datetime(2026, 3, 1),
                    "trait_focus": "curiosity",
                    "current_version": 1,
                    "reader_world_id": 1,
                    "world_id": 2,
                    "world_name": "Dream",
                    "custom_world_name": None,
                    "published": False,
                    "epub_url": None,
                    "epub_created_at": None,
                },
                {
                    "story_id": 11,
                    "title": "Latest Story",
                    "updated_at": datetime(2026, 3, 2),
                    "created_at": datetime(2026, 3, 2),
                    "trait_focus": "courage",
                    "current_version": 1,
                    "reader_world_id": 1,
                    "world_id": 2,
                    "world_name": "Dream",
                    "custom_world_name": None,
                    "published": False,
                    "epub_url": None,
                    "epub_created_at": None,
                },
            ],
        }

        adaptive_profile = {
            "proficiency": "growing",
            "recommended_story_difficulty": 2,
            "recommended_game_difficulty": 3,
        }
        recommendations = {
            "recommended_words": [
                {"word_id": 5, "word": "brave", "difficulty_level": 1, "mastery_level": 1, "last_seen": None}
            ]
        }
        practice_words = [{"word_id": 5}, {"word_id": 6}]
        vocabulary = [{"word_id": 5, "mastery_level": 1}, {"word_id": 6, "mastery_level": 3}]
        game_history = [{"game_result_id": 3, "game_type": "word_puzzle", "difficulty_level": 2, "score": 80, "duration_seconds": 45, "played_at": None}]
        worlds = [Mock(), Mock()]

        with patch("backend.reader_home.home_service.get_reader", return_value=reader), patch(
            "backend.reader_home.home_service.get_reader_library",
            return_value=library,
        ), patch(
            "backend.reader_home.home_service.get_adaptive_profile",
            return_value=adaptive_profile,
        ), patch(
            "backend.reader_home.home_service.get_recommendations",
            return_value=recommendations,
        ), patch(
            "backend.reader_home.home_service.get_reader_practice_vocabulary",
            return_value=practice_words,
        ), patch(
            "backend.reader_home.home_service.get_reader_vocabulary",
            return_value=vocabulary,
        ), patch(
            "backend.reader_home.home_service.get_game_history",
            return_value=game_history,
        ), patch(
            "backend.reader_home.home_service.list_reader_worlds",
            return_value=worlds,
        ):
            payload = get_reader_home_summary(self.db, 42, 7)

        self.assertEqual(payload["reader"]["name"], "Ari")
        self.assertEqual(payload["continue_reading"]["story_id"], 11)
        self.assertEqual(payload["library_summary"]["story_count"], 2)
        self.assertEqual(payload["library_summary"]["world_count"], 2)
        self.assertEqual(payload["vocabulary_summary"]["practice_words"], 2)
        self.assertEqual(payload["vocabulary_summary"]["mastered_words"], 1)
        self.assertEqual(payload["game_summary"]["recommended_game_difficulty"], 3)


if __name__ == "__main__":
    unittest.main()
