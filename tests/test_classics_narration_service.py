import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from backend.classics.classics_narration_service import generate_classics_narration, generate_story_narration_payload


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

    def test_default_run_expands_author_filters(self) -> None:
        with patch(
            "backend.classics.classics_narration_service.list_classical_story_candidates",
            return_value=[],
        ) as list_candidates:
            summary = generate_classics_narration(self.db)

        self.assertEqual(summary.processed, 0)
        authors = list_candidates.call_args.kwargs["authors"]
        self.assertIn("Aesop", authors)
        self.assertIn("Hans Christian Andersen", authors)
        self.assertIn("Brothers Grimm", authors)
        self.assertIn("The Children's Bible", authors)

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

    def test_continue_on_error_processes_remaining_stories(self) -> None:
        first_story = build_story(11)
        second_story = build_story(12)
        third_story = build_story(13)

        with patch(
            "backend.classics.classics_narration_service.list_classical_story_candidates",
            return_value=[first_story, second_story, third_story],
        ), patch(
            "backend.classics.classics_narration_service._has_valid_polly_narration",
            return_value=False,
        ), patch(
            "backend.classics.classics_narration_service._has_valid_classics_illustrations",
            return_value=True,
        ), patch(
            "backend.classics.classics_narration_service.generate_story_narration_payload",
            side_effect=[{"mode": "polly"}, HTTPException(status_code=500, detail="boom"), {"mode": "polly"}],
        ), patch("backend.classics.classics_narration_service.update_classical_story_narration"):
            summary = generate_classics_narration(self.db, limit=3, continue_on_error=True)

        self.assertEqual(summary.processed, 3)
        self.assertEqual(summary.generated, 2)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(summary.narration_generated, 2)
        self.assertEqual(self.db.commit.call_count, 2)
        self.assertEqual(self.db.rollback.call_count, 1)

    def test_generate_story_narration_payload_chunks_long_stories(self) -> None:
        story = build_story(99)
        long_units = [
            {
                "unit_id": "classic-99-1",
                "unit_order": 1,
                "unit_type": "paragraph",
                "text": ("One " * 450).strip(),
            },
            {
                "unit_id": "classic-99-2",
                "unit_order": 2,
                "unit_type": "paragraph",
                "text": ("Two " * 450).strip(),
            },
        ]

        first_synthesis = SimpleNamespace(
            audio_bytes=b"audio-one",
            speech_marks_raw='{"time":0,"type":"word","start":0,"end":4,"value":"One"}\n',
            voice_plan=SimpleNamespace(
                voice_id="Joanna",
                engine="neural",
                sample_rate="24000",
                output_format="mp3",
            ),
        )
        second_synthesis = SimpleNamespace(
            audio_bytes=b"audio-two",
            speech_marks_raw='{"time":0,"type":"word","start":0,"end":4,"value":"Two"}\n',
            voice_plan=first_synthesis.voice_plan,
        )

        polly_client = Mock()
        polly_client.synthesize_storytelling_narration.side_effect = [first_synthesis, second_synthesis]
        audio_storage = Mock()
        audio_storage.save_story_audio.return_value = "/media/classics-audio/story_99.mp3"

        with patch("backend.classics.classics_narration_service.build_base_read_units", return_value=long_units):
            payload = generate_story_narration_payload(
                story=story,
                voice="Joanna",
                polly_client=polly_client,
                audio_storage=audio_storage,
            )

        self.assertEqual(polly_client.synthesize_storytelling_narration.call_count, 2)
        audio_storage.save_story_audio.assert_called_once_with(99, b"audio-oneaudio-two")
        self.assertEqual(payload["audio_url"], "/media/classics-audio/story_99.mp3")
        self.assertEqual(len(payload["units"]), 2)
        self.assertEqual(payload["units"][0]["audio_start_ms"], 0)
        self.assertGreaterEqual(payload["units"][1]["audio_start_ms"], payload["units"][0]["audio_end_ms"])


if __name__ == "__main__":
    unittest.main()
