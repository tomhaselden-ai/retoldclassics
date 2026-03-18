import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from backend.parent_pin.pin_repository import ParentPinSessionRecord, ParentPinStateRecord
from backend.parent_pin.pin_service import (
    PARENT_PIN_LOCKOUT_MINUTES,
    PARENT_PIN_MAX_FAILED_ATTEMPTS,
    ParentPinError,
    clear_parent_pin_session,
    get_parent_pin_status,
    hash_parent_pin,
    set_parent_pin,
    verify_parent_pin,
)


def build_state(
    *,
    enabled: bool,
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    pin_hash: str | None = None,
) -> ParentPinStateRecord:
    return ParentPinStateRecord(
        account_id=42,
        parent_pin_hash=pin_hash,
        parent_pin_enabled=enabled,
        failed_pin_attempts=failed_attempts,
        parent_pin_locked_until=locked_until,
    )


class ParentPinServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()

    def test_set_parent_pin_creates_verified_session(self) -> None:
        with patch(
            "backend.parent_pin.pin_service.get_parent_pin_state",
            side_effect=[build_state(enabled=False), build_state(enabled=True, pin_hash="hash")],
        ), patch(
            "backend.parent_pin.pin_service.update_parent_pin_state"
        ) as update_state, patch(
            "backend.parent_pin.pin_service.create_parent_pin_session"
        ) as create_session:
            payload = set_parent_pin(self.db, 42, "1234")

        self.assertEqual(payload["status"], "pin_set")
        self.assertTrue(payload["pin_enabled"])
        self.assertTrue(payload["verified"])
        self.assertIn("session_token", payload)
        update_state.assert_called_once()
        create_session.assert_called_once()
        self.db.commit.assert_called_once()

    def test_verify_parent_pin_returns_verified_status_for_valid_pin(self) -> None:
        pin_hash = hash_parent_pin("1234")
        with patch(
            "backend.parent_pin.pin_service.get_parent_pin_state",
            side_effect=[build_state(enabled=True, pin_hash=pin_hash), build_state(enabled=True, pin_hash=pin_hash)],
        ), patch("backend.parent_pin.pin_service.update_parent_pin_state") as update_state, patch(
            "backend.parent_pin.pin_service.create_parent_pin_session"
        ) as create_session:
            payload = verify_parent_pin(self.db, 42, "1234")

        self.assertEqual(payload["status"], "verified")
        self.assertTrue(payload["verified"])
        update_state.assert_called_once()
        create_session.assert_called_once()
        self.db.commit.assert_called_once()

    def test_verify_parent_pin_locks_after_max_failed_attempts(self) -> None:
        pin_hash = hash_parent_pin("1234")
        with patch(
            "backend.parent_pin.pin_service.get_parent_pin_state",
            return_value=build_state(enabled=True, pin_hash=pin_hash, failed_attempts=PARENT_PIN_MAX_FAILED_ATTEMPTS - 1),
        ), patch("backend.parent_pin.pin_service.update_parent_pin_state") as update_state:
            with self.assertRaises(ParentPinError) as raised:
                verify_parent_pin(self.db, 42, "0000")

        self.assertEqual(raised.exception.error_code, "parent_pin_locked")
        self.assertEqual(raised.exception.status_code, 423)
        self.db.commit.assert_called_once()
        locked_until = update_state.call_args.kwargs["parent_pin_locked_until"]
        self.assertIsNotNone(locked_until)
        self.assertGreaterEqual(
            locked_until,
            datetime.now(timezone.utc) + timedelta(minutes=PARENT_PIN_LOCKOUT_MINUTES - 1),
        )

    def test_get_parent_pin_status_reports_verified_session(self) -> None:
        now = datetime.now(timezone.utc)
        state = build_state(enabled=True, pin_hash=hash_parent_pin("1234"))
        session = ParentPinSessionRecord(
            session_id=3,
            account_id=42,
            session_token="pin-session",
            created_at=now,
            expires_at=now + timedelta(hours=2),
            revoked_at=None,
        )
        with patch("backend.parent_pin.pin_service.get_parent_pin_state", return_value=state), patch(
            "backend.parent_pin.pin_service.get_parent_pin_session",
            return_value=session,
        ):
            payload = get_parent_pin_status(self.db, 42, "pin-session")

        self.assertTrue(payload["pin_enabled"])
        self.assertTrue(payload["verified"])
        self.assertIsNotNone(payload["session_expires_at"])

    def test_get_parent_pin_status_ignores_expired_session(self) -> None:
        now = datetime.now(timezone.utc)
        state = build_state(enabled=True, pin_hash=hash_parent_pin("1234"))
        session = ParentPinSessionRecord(
            session_id=3,
            account_id=42,
            session_token="pin-session",
            created_at=now - timedelta(hours=3),
            expires_at=now - timedelta(minutes=5),
            revoked_at=None,
        )
        with patch("backend.parent_pin.pin_service.get_parent_pin_state", return_value=state), patch(
            "backend.parent_pin.pin_service.get_parent_pin_session",
            return_value=session,
        ):
            payload = get_parent_pin_status(self.db, 42, "pin-session")

        self.assertTrue(payload["pin_enabled"])
        self.assertFalse(payload["verified"])
        self.assertIsNone(payload["session_expires_at"])

    def test_clear_parent_pin_session_revokes_session(self) -> None:
        with patch("backend.parent_pin.pin_service.revoke_parent_pin_session") as revoke_session:
            payload = clear_parent_pin_session(self.db, 42, "pin-session")

        self.assertEqual(payload["status"], "cleared")
        revoke_session.assert_called_once()
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
