import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.games.game_session_service import (
    GameSessionServiceError,
    complete_v1_game_session,
    create_v1_game_session,
    get_game_catalog,
    get_v1_game_session,
)


def build_session(*, status: str = "ready", completion_status: str = "in_progress") -> SimpleNamespace:
    return SimpleNamespace(
        session_id=9,
        account_id=42,
        reader_id=7,
        game_type="build_the_word",
        source_type="story",
        source_story_id=12,
        difficulty_level=2,
        status=status,
        item_count=4,
        words_attempted=0,
        words_correct=0,
        words_incorrect=0,
        hints_used=0,
        completion_status=completion_status,
        started_at=datetime(2026, 3, 17, 10, 0, 0),
        ended_at=None,
        duration_seconds=None,
        session_payload={
            "version": 1,
            "game_type": "build_the_word",
            "difficulty_level": 2,
            "item_count": 4,
            "items": [
                {
                    "word_id": 1,
                    "word": "Lantern",
                    "definition": "A lamp with a handle.",
                    "example_sentence": "The lantern glowed at dusk.",
                    "difficulty_level": 2,
                    "reader_id": 7,
                    "story_id": 12,
                    "source_type": "story",
                    "trait_focus": "curiosity",
                }
            ],
            "rounds": [],
        },
        created_at=datetime(2026, 3, 17, 10, 0, 0),
        updated_at=datetime(2026, 3, 17, 10, 0, 0),
    )


class GameSessionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_get_game_catalog_uses_reader_scope(self) -> None:
        with patch(
            "backend.games.game_session_service.get_reader_for_account",
            return_value=SimpleNamespace(reader_id=7),
        ) as reader_mocked, patch(
            "backend.games.game_session_service.list_recent_game_results",
            return_value=[],
        ), patch(
            "backend.games.game_session_service.list_recent_game_sessions_for_reader",
            return_value=[],
        ):
            payload = get_game_catalog(self.db, 42, 7)

        self.assertEqual(payload["reader_id"], 7)
        self.assertEqual(len(payload["games"]), 6)
        reader_mocked.assert_called_once_with(self.db, 7, 42)

    def test_create_v1_game_session_returns_shared_items_and_payload(self) -> None:
        practice_item = SimpleNamespace(
            word_id=1,
            word="Lantern",
            definition="A lamp with a handle.",
            example_sentence="The lantern glowed at dusk.",
            difficulty_level=2,
            reader_id=7,
            story_id=12,
            source_type="story",
            trait_focus="curiosity",
        )
        story_item = SimpleNamespace(
            word_id=2,
            word="Harbor",
            definition="A sheltered place for boats.",
            example_sentence="The harbor shimmered at dawn.",
            difficulty_level=2,
            reader_id=7,
            story_id=12,
            source_type="story",
            trait_focus="curiosity",
        )
        global_item = SimpleNamespace(
            word_id=3,
            word="Meadow",
            definition="A grassy field.",
            example_sentence=None,
            difficulty_level=2,
            reader_id=7,
            story_id=None,
            source_type="global_vocab",
            trait_focus=None,
        )
        global_item_two = SimpleNamespace(
            word_id=4,
            word="Pebble",
            definition="A small smooth stone.",
            example_sentence="A pebble skipped across the pond.",
            difficulty_level=2,
            reader_id=7,
            story_id=None,
            source_type="global_vocab",
            trait_focus=None,
        )

        with patch(
            "backend.games.game_session_service.get_reader_for_account",
            return_value=SimpleNamespace(reader_id=7),
        ), patch(
            "backend.games.game_session_service.get_story_for_reader",
            return_value=SimpleNamespace(story_id=12),
        ), patch(
            "backend.games.game_session_service.list_recent_game_results",
            return_value=[],
        ), patch(
            "backend.games.game_session_service.list_reader_story_word_items",
            side_effect=[[practice_item, story_item], [practice_item, story_item]],
        ), patch(
            "backend.games.game_session_service.list_reader_practice_word_items",
            return_value=[practice_item, story_item],
        ), patch(
            "backend.games.game_session_service.list_global_word_items",
            return_value=[global_item, global_item_two],
        ), patch(
            "backend.games.game_session_service.create_game_session",
            return_value=9,
        ) as create_mocked, patch(
            "backend.games.game_session_service.get_game_session_for_account",
            return_value=build_session(),
        ):
            payload = create_v1_game_session(
                self.db,
                42,
                7,
                game_type="build_the_word",
                story_id=12,
                difficulty_level=2,
                item_count=4,
            )

        self.assertEqual(payload["session_id"], 9)
        self.assertEqual(payload["game_type"], "build_the_word")
        self.assertGreaterEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["word"], "Lantern")
        self.assertEqual(payload["payload"]["game_type"], "build_the_word")
        self.assertGreaterEqual(len(payload["payload"]["rounds"]), 2)
        self.assertIn("figure_steps", payload["payload"])
        self.assertEqual(payload["payload"]["launch_config"]["launch_mode"], "custom")
        create_mocked.assert_called_once()
        self.assertEqual(create_mocked.call_args.kwargs["session_payload"]["game_type"], "build_the_word")
        self.db.commit.assert_called_once()

    def test_create_v1_game_session_auto_selects_launch_settings(self) -> None:
        practice_item = SimpleNamespace(
            word_id=1,
            word="Lantern",
            definition="A lamp with a handle.",
            example_sentence="The lantern glowed at dusk.",
            difficulty_level=2,
            reader_id=7,
            story_id=12,
            source_type="story",
            trait_focus="curiosity",
        )
        story_item = SimpleNamespace(
            word_id=2,
            word="Harbor",
            definition="A sheltered place for boats.",
            example_sentence="The harbor shimmered at dawn.",
            difficulty_level=2,
            reader_id=7,
            story_id=12,
            source_type="story",
            trait_focus="curiosity",
        )
        extra_items = [
            SimpleNamespace(
                word_id=index,
                word=word,
                definition=f"Definition for {word}.",
                example_sentence=None,
                difficulty_level=1,
                reader_id=7,
                story_id=12,
                source_type="story",
                trait_focus="curiosity",
            )
            for index, word in ((3, "Meadow"), (4, "Pebble"), (5, "Willow"), (6, "Comet"))
        ]

        with patch(
            "backend.games.game_session_service.get_reader_for_account",
            return_value=SimpleNamespace(reader_id=7),
        ), patch(
            "backend.games.game_session_service.get_latest_story_for_reader",
            return_value=SimpleNamespace(story_id=12),
        ), patch(
            "backend.games.game_session_service.list_recent_game_results",
            return_value=[],
        ), patch(
            "backend.games.game_session_service.list_reader_story_word_items",
            side_effect=[[practice_item, story_item, *extra_items], [practice_item, story_item, *extra_items]],
        ), patch(
            "backend.games.game_session_service.list_reader_practice_word_items",
            return_value=[practice_item, story_item],
        ), patch(
            "backend.games.game_session_service.list_global_word_items",
            return_value=[],
        ), patch(
            "backend.games.game_session_service.create_game_session",
            return_value=9,
        ):
            session = build_session()
            session.game_type = "crossword"
            session.source_story_id = 12
            session.session_payload = {
                "version": 1,
                "game_type": "crossword",
                "difficulty_level": 1,
                "item_count": 4,
                "items": [
                    {
                        "word_id": 1,
                        "word": "Lantern",
                        "definition": "A lamp with a handle.",
                        "example_sentence": "The lantern glowed at dusk.",
                        "difficulty_level": 1,
                        "reader_id": 7,
                        "story_id": 12,
                        "source_type": "story",
                        "trait_focus": "curiosity",
                    }
                ],
                "crossword": {"rows": 1, "columns": 1, "cells": [], "entries": [], "across_clues": [], "down_clues": []},
                "launch_config": {"launch_mode": "auto", "source_reason": "recent_story"},
            }
            with patch(
                "backend.games.game_session_service.get_game_session_for_account",
                return_value=session,
            ):
                payload = create_v1_game_session(
                    self.db,
                    42,
                    7,
                    game_type="crossword",
                )

        self.assertEqual(payload["game_type"], "crossword")
        self.assertEqual(payload["source_type"], "story")
        self.assertEqual(payload["source_story_id"], 12)
        self.assertEqual(payload["payload"]["launch_config"]["launch_mode"], "auto")
        self.assertEqual(payload["payload"]["launch_config"]["source_reason"], "recent_story")

    def test_complete_v1_game_session_records_attempts_and_legacy_result(self) -> None:
        completed_session = build_session(status="completed", completion_status="completed")
        completed_session.words_attempted = 2
        completed_session.words_correct = 1
        completed_session.words_incorrect = 1
        completed_session.hints_used = 1
        completed_session.duration_seconds = 55

        with patch(
            "backend.games.game_session_service.get_game_session_for_account",
            side_effect=[build_session(), completed_session],
        ), patch(
            "backend.games.game_session_service.replace_word_attempts"
        ) as replace_mocked, patch(
            "backend.games.game_session_service.update_game_session_completion"
        ) as update_mocked, patch(
            "backend.games.game_session_service.insert_game_result",
            return_value=17,
        ):
            payload = complete_v1_game_session(
                self.db,
                42,
                7,
                9,
                completion_status="completed",
                duration_seconds=55,
                attempts=[
                    {
                        "word_id": 1,
                        "word_text": "Lantern",
                        "attempt_count": 2,
                        "correct": True,
                        "time_spent_seconds": 12,
                        "hint_used": False,
                        "skipped": False,
                    },
                    {
                        "word_id": 2,
                        "word_text": "Meadow",
                        "attempt_count": 1,
                        "correct": False,
                        "time_spent_seconds": 8,
                        "hint_used": True,
                        "skipped": False,
                    },
                ],
            )

        self.assertEqual(payload["legacy_game_result_id"], 17)
        self.assertEqual(payload["words_attempted"], 2)
        self.assertEqual(payload["words_correct"], 1)
        self.assertEqual(payload["words_incorrect"], 1)
        self.assertEqual(payload["hints_used"], 1)
        replace_mocked.assert_called_once()
        update_mocked.assert_called_once()
        self.db.commit.assert_called_once()

    def test_complete_v1_game_session_rejects_missing_attempts(self) -> None:
        with self.assertRaises(GameSessionServiceError) as raised:
            complete_v1_game_session(
                self.db,
                42,
                7,
                9,
                completion_status="completed",
                duration_seconds=55,
                attempts=[],
            )

        self.assertEqual(raised.exception.error_code, "invalid_input")

    def test_get_v1_game_session_returns_persisted_payload_items(self) -> None:
        with patch(
            "backend.games.game_session_service.get_game_session_for_account",
            return_value=build_session(),
        ), patch(
            "backend.games.game_session_service.list_word_attempts_for_session",
            return_value=[],
        ):
            payload = get_v1_game_session(self.db, 42, 7, 9)

        self.assertEqual(payload["session_id"], 9)
        self.assertEqual(payload["payload"]["game_type"], "build_the_word")
        self.assertEqual(payload["items"][0]["word"], "Lantern")


if __name__ == "__main__":
    unittest.main()
