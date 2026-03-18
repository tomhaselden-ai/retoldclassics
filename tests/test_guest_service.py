import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.guest.guest_repository import GuestSessionRecord
from backend.guest.guest_service import (
    GUEST_ALLOWED_AUTHORS,
    GUEST_CLASSIC_READ_LIMIT,
    GUEST_GAME_LAUNCH_LIMIT,
    GuestServiceError,
    generate_guest_classic_preview_session,
    get_guest_limits,
    get_guest_classic_story_read,
    start_guest_session,
)


def build_session() -> GuestSessionRecord:
    return GuestSessionRecord(
        session_id=7,
        session_token="guest-token",
        last_ip="127.0.0.1",
        created_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )


class GuestServiceTests(unittest.TestCase):
    def test_guest_allowed_authors_include_bible(self) -> None:
        self.assertIn("Bible", GUEST_ALLOWED_AUTHORS)

    def setUp(self) -> None:
        self.db = Mock()
        self.story = SimpleNamespace(
            story_id=11,
            source_author="Hans Christian Andersen",
            title="The Brave Teacup",
        )

    def test_guest_classic_read_records_first_story_open_and_returns_limits(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.get_classical_story",
            return_value=self.story,
        ), patch("backend.guest.guest_service.has_guest_classic_read", return_value=False), patch(
            "backend.guest.guest_service.count_guest_classic_reads",
            return_value=0,
        ), patch("backend.guest.guest_service.insert_guest_usage_event") as insert_event, patch(
            "backend.guest.guest_service.build_read_payload",
            return_value={"story_id": 11, "title": "The Brave Teacup", "units": []},
        ), patch(
            "backend.guest.guest_service.get_guest_limits",
            return_value={"classics_reads_remaining": 2, "game_launches_remaining": 2},
        ):
            payload = get_guest_classic_story_read(self.db, "guest-token", 11, "127.0.0.1")

        self.assertEqual(payload["guest_limits"]["classics_reads_remaining"], 2)
        insert_event.assert_called_once_with(
            self.db,
            7,
            "classic_read",
            story_id=11,
            metadata_json={"source_author": "Andersen"},
        )
        self.db.commit.assert_called_once()

    def test_guest_classic_read_blocks_when_limit_is_used(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.get_classical_story",
            return_value=self.story,
        ), patch("backend.guest.guest_service.has_guest_classic_read", return_value=False), patch(
            "backend.guest.guest_service.count_guest_classic_reads",
            return_value=GUEST_CLASSIC_READ_LIMIT,
        ):
            with self.assertRaises(GuestServiceError) as raised:
                get_guest_classic_story_read(self.db, "guest-token", 11, "127.0.0.1")

        self.assertEqual(raised.exception.error_code, "guest_classic_limit_reached")
        self.assertEqual(raised.exception.status_code, 403)
        self.db.rollback.assert_called_once()

    def test_guest_preview_records_launch_and_returns_v1_payload(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.count_guest_game_launches",
            return_value=0,
        ), patch("backend.guest.guest_service.get_classical_story", return_value=self.story), patch(
            "backend.guest.guest_service.build_read_payload",
            return_value={"units": [{"text": "Golden lantern garden adventure curious morning forest wonder."}]},
        ), patch("backend.guest.guest_service.extract_preview_text", return_value="A bright preview."), patch(
            "backend.guest.guest_service.insert_guest_usage_event"
        ) as insert_event, patch(
            "backend.guest.guest_service.get_guest_limits",
            return_value={"classics_reads_remaining": 3, "game_launches_remaining": 1},
        ):
            payload = generate_guest_classic_preview_session(self.db, "guest-token", 11, 3, "127.0.0.1")

        self.assertEqual(payload["game_type"], "build_the_word")
        self.assertEqual(payload["payload"]["game_type"], "build_the_word")
        self.assertEqual(len(payload["payload"]["rounds"]), 3)
        insert_event.assert_called_once_with(
            self.db,
            7,
            "game_launch",
            story_id=11,
            metadata_json={"game_type": "build_the_word", "source_type": "classics"},
        )
        self.db.commit.assert_called_once()

    def test_guest_preview_blocks_when_launch_limit_is_used(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.count_guest_game_launches",
            return_value=GUEST_GAME_LAUNCH_LIMIT,
        ):
            with self.assertRaises(GuestServiceError) as raised:
                generate_guest_classic_preview_session(self.db, "guest-token", 11, 5, "127.0.0.1")

        self.assertEqual(raised.exception.error_code, "guest_game_limit_reached")
        self.assertEqual(raised.exception.status_code, 403)
        self.db.rollback.assert_called_once()

    def test_start_guest_session_reuses_existing_valid_session(self) -> None:
        session = build_session()
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=session), patch(
            "backend.guest.guest_service.count_guest_classic_reads",
            return_value=1,
        ), patch(
            "backend.guest.guest_service.count_guest_game_launches",
            return_value=1,
        ):
            payload = start_guest_session(self.db, "guest-token", "127.0.0.1")

        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["session_token"], "guest-token")
        self.assertEqual(payload["classics_reads_remaining"], 2)
        self.assertEqual(payload["game_launches_remaining"], 1)

    def test_guest_classic_reread_does_not_consume_additional_limit(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.get_classical_story",
            return_value=self.story,
        ), patch("backend.guest.guest_service.has_guest_classic_read", return_value=True), patch(
            "backend.guest.guest_service.build_read_payload",
            return_value={"story_id": 11, "title": "The Brave Teacup", "units": []},
        ), patch(
            "backend.guest.guest_service.get_guest_limits",
            return_value={"classics_reads_remaining": 1, "game_launches_remaining": 2},
        ), patch("backend.guest.guest_service.insert_guest_usage_event") as insert_event:
            payload = get_guest_classic_story_read(self.db, "guest-token", 11, "127.0.0.1")

        self.assertEqual(payload["guest_limits"]["classics_reads_remaining"], 1)
        insert_event.assert_not_called()

    def test_get_guest_limits_returns_snapshot_for_active_session(self) -> None:
        with patch("backend.guest.guest_service._get_active_guest_session", return_value=build_session()), patch(
            "backend.guest.guest_service.count_guest_classic_reads",
            return_value=2,
        ), patch(
            "backend.guest.guest_service.count_guest_game_launches",
            return_value=1,
        ):
            payload = get_guest_limits(self.db, "guest-token", "127.0.0.1")

        self.assertEqual(payload["classics_reads_used"], 2)
        self.assertEqual(payload["game_launches_used"], 1)
        self.assertEqual(payload["classics_reads_remaining"], 1)


if __name__ == "__main__":
    unittest.main()
