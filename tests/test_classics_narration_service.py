import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from backend.classics.classics_narration_service import generate_classics_narration


def build_story(story_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        story_id=story_id,
        source_author="Andersen",
        title=f"Story {story_id}",
        narration=None,
        illustration_prompts=None,
    )


class ClassicsNarrationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_generated_story_commits_after_each_story(self) -> None:
        story = build_story(11)

        with patch("backend.classics.classics_narration_service.list_classical_story_candidates", return_value=[story]), patch(
            "backend.classics.classics_narration_service._has_valid_polly_narration",
            return_value=False,
        ), patch(
            "backend.classics.classics_narration_service._has_valid_classics_illustrations",
            return_value=False,
        ), patch(
            "backend.classics.classics_narration_service.generate_story_narration_payload",
            return_value={"mode": "polly"},
        ), patch(
            "backend.classics.classics_narration_service.generate_story_illustration_payload",
            return_value={"mode": "generated"},
        ), patch("backend.classics.classics_narration_service.update_classical_story_narration") as update_narration, patch(
            "backend.classics.classics_narration_service.update_classical_story_illustrations"
        ) as update_illustration:
            summary = generate_classics_narration(self.db, limit=1)

        self.assertEqual(summary.generated, 1)
        self.assertEqual(summary.narration_generated, 1)
        self.assertEqual(summary.illustrations_generated, 1)
        update_narration.assert_called_once()
        update_illustration.assert_called_once()
        self.db.commit.assert_called_once()

    def test_skipped_story_does_not_commit(self) -> None:
        story = build_story(11)

        with patch("backend.classics.classics_narration_service.list_classical_story_candidates", return_value=[story]), patch(
            "backend.classics.classics_narration_service._has_valid_polly_narration",
            return_value=True,
        ), patch(
            "backend.classics.classics_narration_service._has_valid_classics_illustrations",
            return_value=True,
        ):
            summary = generate_classics_narration(self.db, limit=1)

        self.assertEqual(summary.skipped, 1)
        self.db.commit.assert_not_called()

    def test_failure_rolls_back_only_current_story_after_prior_commit(self) -> None:
        first_story = build_story(11)
        second_story = build_story(12)

        with patch(
            "backend.classics.classics_narration_service.list_classical_story_candidates",
            return_value=[first_story, second_story],
        ), patch(
            "backend.classics.classics_narration_service._has_valid_polly_narration",
            return_value=False,
        ), patch(
            "backend.classics.classics_narration_service._has_valid_classics_illustrations",
            return_value=True,
        ), patch(
            "backend.classics.classics_narration_service.generate_story_narration_payload",
            side_effect=[{"mode": "polly"}, HTTPException(status_code=500, detail="boom")],
        ), patch("backend.classics.classics_narration_service.update_classical_story_narration"):
            with self.assertRaises(HTTPException):
                generate_classics_narration(self.db, limit=2)

        self.assertEqual(self.db.commit.call_count, 1)
        self.assertEqual(self.db.rollback.call_count, 1)


if __name__ == "__main__":
    unittest.main()
