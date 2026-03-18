import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.games.game_reporting_service import (
    GameReportingServiceError,
    get_account_game_practice_summary,
    get_reader_game_practice_summary,
)


def build_session(
    *,
    session_id: int,
    game_type: str,
    words_attempted: int,
    words_correct: int,
    duration_seconds: int,
    started_at: datetime,
) -> SimpleNamespace:
    return SimpleNamespace(
        session_id=session_id,
        account_id=42,
        reader_id=7,
        game_type=game_type,
        source_type="story",
        source_story_id=12,
        difficulty_level=2,
        status="completed",
        item_count=8,
        words_attempted=words_attempted,
        words_correct=words_correct,
        words_incorrect=max(0, words_attempted - words_correct),
        hints_used=0,
        completion_status="completed",
        started_at=started_at,
        ended_at=started_at + timedelta(minutes=3),
        duration_seconds=duration_seconds,
        session_payload=None,
        created_at=started_at,
        updated_at=started_at,
    )


def build_attempt(
    *,
    session_id: int,
    word_text: str,
    correct: bool,
    skipped: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        attempt_id=1,
        session_id=session_id,
        word_id=None,
        word_text=word_text,
        game_type="build_the_word",
        attempt_count=1,
        correct=correct,
        time_spent_seconds=5,
        hint_used=False,
        skipped=skipped,
        created_at=datetime.now(timezone.utc),
    )


class GameReportingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_reader_game_practice_summary_aggregates_active_session_data(self) -> None:
        now = datetime.now(timezone.utc)
        sessions = [
            build_session(
                session_id=1,
                game_type="build_the_word",
                words_attempted=4,
                words_correct=3,
                duration_seconds=90,
                started_at=now - timedelta(days=1),
            ),
            build_session(
                session_id=2,
                game_type="word_scramble",
                words_attempted=4,
                words_correct=2,
                duration_seconds=120,
                started_at=now - timedelta(days=10),
            ),
            build_session(
                session_id=3,
                game_type="build_the_word",
                words_attempted=4,
                words_correct=4,
                duration_seconds=80,
                started_at=now - timedelta(days=2),
            ),
            build_session(
                session_id=4,
                game_type="flash_cards",
                words_attempted=4,
                words_correct=3,
                duration_seconds=70,
                started_at=now - timedelta(days=3),
            ),
        ]
        attempts = [
            build_attempt(session_id=1, word_text="Lantern", correct=False),
            build_attempt(session_id=1, word_text="Lantern", correct=False),
            build_attempt(session_id=2, word_text="Harbor", correct=False),
            build_attempt(session_id=3, word_text="Lantern", correct=True),
        ]

        with patch("backend.games.game_reporting_service.get_reader_for_account", return_value=SimpleNamespace(reader_id=7)), patch(
            "backend.games.game_reporting_service.list_game_sessions_for_account",
            return_value=sessions,
        ), patch(
            "backend.games.game_reporting_service.list_word_attempts_for_sessions",
            return_value=attempts,
        ):
            summary = get_reader_game_practice_summary(self.db, 42, 7)

        self.assertEqual(summary["sessions_total"], 4)
        self.assertEqual(summary["sessions_this_week"], 3)
        self.assertEqual(summary["words_practiced"], 16)
        self.assertEqual(summary["words_correct"], 12)
        self.assertEqual(summary["average_success_rate"], 75.0)
        self.assertEqual(summary["practice_time_seconds"], 360)
        self.assertEqual(summary["strongest_game_type"], "build_the_word")
        self.assertIsNotNone(summary["weakest_game_type"])
        self.assertEqual(summary["repeated_missed_words"][0]["word_text"], "Lantern")
        self.assertEqual(summary["repeated_missed_words"][0]["miss_count"], 2)
        self.assertEqual(len(summary["accuracy_by_game_type"]), 3)

    def test_reader_game_practice_summary_rejects_missing_reader(self) -> None:
        with patch("backend.games.game_reporting_service.get_reader_for_account", return_value=None):
            with self.assertRaises(GameReportingServiceError) as raised:
                get_reader_game_practice_summary(self.db, 42, 7)

        self.assertEqual(raised.exception.error_code, "missing_resource")

    def test_account_game_practice_summary_handles_empty_history(self) -> None:
        with patch("backend.games.game_reporting_service.list_game_sessions_for_account", return_value=[]), patch(
            "backend.games.game_reporting_service.list_word_attempts_for_sessions",
            return_value=[],
        ):
            summary = get_account_game_practice_summary(self.db, 42)

        self.assertEqual(summary["sessions_total"], 0)
        self.assertEqual(summary["average_success_rate"], None)
        self.assertEqual(summary["accuracy_by_game_type"], [])
        self.assertEqual(summary["repeated_missed_words"], [])


if __name__ == "__main__":
    unittest.main()
