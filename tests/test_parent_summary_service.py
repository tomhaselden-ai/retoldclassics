import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.parent.summary_service import get_parent_reader_summary, get_parent_summary
from backend.readers.reader_service import ReaderRecord


class ParentSummaryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_get_parent_summary_merges_reader_records_with_learning_insights(self) -> None:
        reader = ReaderRecord(
            reader_id=7,
            account_id=42,
            name="Ari",
            age=8,
            reading_level="developing",
            gender_preference="any",
            trait_focus=["curiosity", "courage"],
            created_at=datetime(2026, 3, 1),
        )
        insights = {
            "reader_count": 1,
            "aggregate_statistics": {
                "stories_read": 12,
                "words_mastered": 45,
                "tracked_words": 60,
                "games_played": 9,
                "average_game_score": 84.5,
            },
            "readers": [
                {
                    "reader_id": 7,
                    "name": "Ari",
                    "reading_level": "developing",
                    "proficiency": "growing",
                    "stories_read": 12,
                    "words_mastered": 45,
                    "average_game_score": 84.5,
                    "strengths": ["Pattern recognition"],
                    "focus_areas": [{"message": "Practice multi-step recall"}],
                    "recommendations": {
                        "recommended_story_difficulty": 2,
                        "recommended_vocabulary_difficulty": 2,
                        "recommended_game_difficulty": 3,
                    },
                }
            ],
        }

        with patch("backend.parent.summary_service.list_readers", return_value=[reader]), patch(
            "backend.parent.summary_service.get_account_learning_insights",
            return_value=insights,
        ):
            payload = get_parent_summary(self.db, 42)

        self.assertEqual(payload["account_id"], 42)
        self.assertEqual(payload["reader_count"], 1)
        self.assertEqual(payload["readers"][0]["name"], "Ari")
        self.assertEqual(payload["readers"][0]["age"], 8)
        self.assertEqual(payload["readers"][0]["focus_message"], "Practice multi-step recall")
        self.assertEqual(payload["readers"][0]["recommended_game_difficulty"], 3)

    def test_get_parent_reader_summary_builds_workspace_payload(self) -> None:
        reader = ReaderRecord(
            reader_id=7,
            account_id=42,
            name="Ari",
            age=8,
            reading_level="developing",
            gender_preference="any",
            trait_focus=["curiosity"],
            created_at=datetime(2026, 3, 1),
        )
        dashboard = {"reading_statistics": {"stories_read": 3, "words_mastered": 10}, "recent_stories": []}
        learning_insights = {"proficiency": "growing", "focus_areas": [], "recommendations": {}}
        library = {"bookshelf_id": 4, "story_count": 2, "stories": [{"story_id": 11}, {"story_id": 12}]}
        world = Mock()
        world.reader_world_id = 5
        world.world_id = 3
        world.custom_name = "Dream Shelf"
        world.world.name = "Dream"
        world.world.description = "A bright starter world"

        with patch("backend.parent.summary_service.get_reader", return_value=reader), patch(
            "backend.parent.summary_service.get_reader_dashboard",
            return_value=dashboard,
        ), patch(
            "backend.parent.summary_service.get_reader_learning_insights",
            return_value=learning_insights,
        ), patch(
            "backend.parent.summary_service.get_reader_library",
            return_value=library,
        ), patch(
            "backend.parent.summary_service.list_reader_worlds",
            return_value=[world],
        ):
            payload = get_parent_reader_summary(self.db, 42, 7)

        self.assertEqual(payload["reader"]["name"], "Ari")
        self.assertEqual(payload["library_summary"]["story_count"], 2)
        self.assertEqual(len(payload["library_summary"]["recent_stories"]), 2)
        self.assertEqual(payload["world_summary"]["world_count"], 1)
        self.assertEqual(payload["world_summary"]["worlds"][0]["name"], "Dream")


if __name__ == "__main__":
    unittest.main()
