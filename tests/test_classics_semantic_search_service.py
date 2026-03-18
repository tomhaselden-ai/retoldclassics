import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.classics.classics_semantic_search_service import discover_classics


class ClassicsSemanticSearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = object()
        self.story = SimpleNamespace(
            story_id=11,
            source_author="Aesop",
            title="The Fox and the Crow",
            age_range="5-8",
            reading_level="early",
            moral="Kindness and caution matter.",
            paragraphs_modern=None,
            scenes=None,
            illustration_prompts=None,
        )

    def test_discover_classics_returns_semantic_matches_when_vector_hits_exist(self) -> None:
        vector_store = SimpleNamespace(
            query=lambda **_: [
                {"metadata": {"story_id": 11, "author": "Aesop"}, "distance": 0.18},
                {"metadata": {"story_id": 11, "author": "Aesop"}, "distance": 0.22},
            ]
        )

        with patch("backend.classics.classics_semantic_search_service.ClassicalStoryVectorStore", return_value=vector_store), patch(
            "backend.classics.classics_semantic_search_service.get_classical_stories_by_ids",
            return_value=[self.story],
        ) as stories_mocked:
            payload = discover_classics(
                self.db,
                authors=["Aesop"],
                query_text="clever foxes",
                limit=12,
                offset=0,
                applied_author="Aesop",
            )

        self.assertEqual(payload["match_mode"], "semantic")
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(payload["items"][0]["story_id"], 11)
        stories_mocked.assert_called_once_with(self.db, [11], ["Aesop"])

    def test_discover_classics_falls_back_to_keyword_search_when_vector_store_fails(self) -> None:
        with patch(
            "backend.classics.classics_semantic_search_service.ClassicalStoryVectorStore",
            side_effect=RuntimeError("vector unavailable"),
        ), patch(
            "backend.classics.classics_semantic_search_service.list_classical_stories",
            return_value=[self.story],
        ) as list_mocked, patch(
            "backend.classics.classics_semantic_search_service.count_classical_stories",
            return_value=1,
        ) as count_mocked:
            payload = discover_classics(
                self.db,
                authors=["Aesop"],
                query_text="kindness",
                limit=12,
                offset=0,
                applied_author="Aesop",
            )

        self.assertEqual(payload["match_mode"], "keyword_fallback")
        self.assertEqual(payload["items"][0]["story_id"], 11)
        list_mocked.assert_called_once_with(self.db, ["Aesop"], "kindness", 12, 0)
        count_mocked.assert_called_once_with(self.db, ["Aesop"], "kindness")

    def test_discover_classics_uses_browse_mode_when_query_is_empty(self) -> None:
        with patch(
            "backend.classics.classics_semantic_search_service.list_classical_stories",
            return_value=[self.story],
        ), patch(
            "backend.classics.classics_semantic_search_service.count_classical_stories",
            return_value=1,
        ):
            payload = discover_classics(
                self.db,
                authors=["Aesop"],
                query_text=None,
                limit=12,
                offset=0,
                applied_author=None,
            )

        self.assertEqual(payload["match_mode"], "browse")
        self.assertEqual(payload["items"][0]["source_author"], "Aesop")


if __name__ == "__main__":
    unittest.main()
