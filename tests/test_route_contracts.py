import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.api.continuity_routes import (
    ReaderWorldContinuityRequest,
    StoryContinuityRequest,
    reader_world_character_continuity_check_route,
    reader_world_continuity_check_route,
    reader_world_story_continuity_check_route,
    story_continuity_check_route,
)
from backend.api.character_canon_routes import (
    CharacterCanonPreviewRequest,
    CharacterCanonSaveRequest,
    enhance_character_canon_preview_route,
    get_character_canon_detail_route,
    get_character_canon_overview_route,
    publish_character_canon_route,
    save_character_canon_route,
)
from backend.api.guest_routes import (
    GuestGameLaunchRequest,
    GuestSessionStartRequest,
    get_guest_classic_story_read_route,
    launch_guest_game_preview_route,
    start_guest_session_route,
)
from backend.api.goal_routes import (
    CreateGoalRequest,
    UpdateGoalRequest,
    create_reader_goal_route,
    get_parent_goals_route,
    get_reader_goals_route,
    update_goal_route,
)
from backend.api.game_routes import (
    GameGenerateRequest,
    GameResultCreateRequest,
    GameSessionCompleteRequest,
    GameSessionStartRequest,
    complete_game_session_route,
    create_game_session_route,
    generate_game_route,
    get_game_catalog_route,
    get_game_session_route,
    get_game_summary_route,
    record_game_result_route,
)
from backend.api.memory_routes import (
    get_reader_world_character_history_route,
    get_reader_world_history_route,
    get_story_memory_route,
)
from backend.api.parent_pin_routes import (
    ParentPinSetRequest,
    ParentPinVerifyRequest,
    clear_parent_pin_session_route,
    get_parent_pin_status_route,
    set_parent_pin_route,
    verify_parent_pin_route,
)
from backend.api.parent_routes import get_parent_analytics_route, get_parent_reader_summary_route, get_parent_summary_route
from backend.api.reader_home_routes import get_reader_home_route


class RouteContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current_account = SimpleNamespace(account_id=42)
        self.db = object()

    def test_story_memory_route_uses_account_id(self) -> None:
        with patch("backend.api.memory_routes.get_story_memory_for_account", return_value=[]) as mocked:
            result = get_story_memory_route(
                story_id=7,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, [])
        mocked.assert_called_once_with(db=self.db, account_id=42, story_id=7)

    def test_reader_world_history_route_uses_reader_world_scope(self) -> None:
        with patch("backend.api.memory_routes.get_reader_world_history", return_value=[]) as mocked:
            result = get_reader_world_history_route(
                reader_id=3,
                world_id=5,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, [])
        mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=3,
            template_world_id=5,
        )

    def test_reader_world_character_history_route_uses_reader_world_scope(self) -> None:
        with patch("backend.api.memory_routes.get_reader_world_character_history", return_value=[]) as mocked:
            result = get_reader_world_character_history_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, [])
        mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=3,
            template_world_id=5,
            character_id=11,
        )

    def test_story_continuity_route_uses_account_scope(self) -> None:
        payload = StoryContinuityRequest(story_id=8, world_id=5, story_summary="A story summary")
        expected = {"continuity_valid": True, "conflicts": []}
        with patch("backend.api.continuity_routes.evaluate_story_continuity_for_account", return_value=expected) as mocked:
            result = story_continuity_check_route(payload=payload, current_account=self.current_account, db=self.db)
        self.assertEqual(result, expected)
        mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            story_id=8,
            world_id=5,
            story_summary="A story summary",
        )

    def test_reader_world_continuity_routes_use_reader_scope(self) -> None:
        payload = ReaderWorldContinuityRequest(story_summary="Planned story")
        expected = {"continuity_valid": True, "conflicts": []}
        with patch("backend.api.continuity_routes.evaluate_reader_world_continuity", return_value=expected) as world_mocked:
            result = reader_world_continuity_check_route(
                reader_id=3,
                world_id=5,
                payload=payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, expected)
        world_mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=3,
            template_world_id=5,
            story_summary="Planned story",
        )

        with patch(
            "backend.api.continuity_routes.evaluate_reader_world_character_continuity",
            return_value=expected,
        ) as char_mocked:
            result = reader_world_character_continuity_check_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                payload=payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, expected)
        char_mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=3,
            template_world_id=5,
            character_id=11,
            story_summary="Planned story",
        )

        with patch("backend.api.continuity_routes.evaluate_reader_world_story_continuity", return_value=expected) as story_mocked:
            result = reader_world_story_continuity_check_route(
                reader_id=3,
                world_id=5,
                story_id=8,
                payload=payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, expected)
        story_mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=3,
            template_world_id=5,
            story_id=8,
            story_summary="Planned story",
        )

    def test_character_canon_routes_use_reader_world_account_scope(self) -> None:
        with patch(
            "backend.api.character_canon_routes.list_reader_world_character_canon_overview",
            return_value={"characters": []},
        ) as overview_mocked:
            result = get_character_canon_overview_route(
                reader_id=3,
                world_id=5,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"characters": []})
        overview_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=3,
            world_id=5,
        )

        with patch(
            "backend.api.character_canon_routes.get_reader_world_character_canon_detail",
            return_value={"canon": {}},
        ) as detail_mocked:
            result = get_character_canon_detail_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"canon": {}})
        detail_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=3,
            world_id=5,
            character_id=11,
        )

        preview_payload = CharacterCanonPreviewRequest(section_mode="visual")
        with patch(
            "backend.api.character_canon_routes.generate_character_canon_preview",
            return_value={"preview_profile": {}},
        ) as preview_mocked:
            result = enhance_character_canon_preview_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                payload=preview_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"preview_profile": {}})
        preview_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=3,
            world_id=5,
            character_id=11,
            section_mode="visual",
            existing_canon=None,
        )

        save_payload = CharacterCanonSaveRequest(updates={"notes": "Ready"}, enhancement_run_id=7)
        with patch(
            "backend.api.character_canon_routes.save_reader_world_character_canon",
            return_value={"canon": {"notes": "Ready"}},
        ) as save_mocked:
            result = save_character_canon_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                payload=save_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"canon": {"notes": "Ready"}})
        save_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=3,
            world_id=5,
            character_id=11,
            updates={"notes": "Ready"},
            enhanced_by=42,
            enhancement_run_id=7,
        )

        with patch(
            "backend.api.character_canon_routes.publish_reader_world_character_canon",
            return_value={"canon": {"source_status": "canonical"}},
        ) as publish_mocked:
            result = publish_character_canon_route(
                reader_id=3,
                world_id=5,
                character_id=11,
                payload=save_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"canon": {"source_status": "canonical"}})
        publish_mocked.assert_called_once_with(
            self.db,
            account_id=42,
            reader_id=3,
            world_id=5,
            character_id=11,
            updates={"notes": "Ready"},
            enhanced_by=42,
            enhancement_run_id=7,
        )

    def test_guest_session_route_passes_existing_token_and_client_ip(self) -> None:
        payload = GuestSessionStartRequest(existing_session_token="guest-token")
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        expected = {"status": "active", "session_token": "guest-token"}

        with patch("backend.api.guest_routes.start_guest_session", return_value=expected) as mocked:
            result = start_guest_session_route(payload=payload, request=request, db=self.db)

        self.assertEqual(result, expected)
        mocked.assert_called_once_with(self.db, "guest-token", "127.0.0.1")

    def test_guest_classic_read_and_quiz_routes_pass_guest_session_header(self) -> None:
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

        with patch("backend.api.guest_routes.get_guest_classic_story_read", return_value={"story_id": 9}) as read_mocked:
            result = get_guest_classic_story_read_route(
                story_id=9,
                request=request,
                guest_session_token="guest-token",
                db=self.db,
            )
        self.assertEqual(result, {"story_id": 9})
        read_mocked.assert_called_once_with(self.db, "guest-token", 9, "127.0.0.1")

        payload = GuestGameLaunchRequest(story_id=9, item_count=5)
        with patch("backend.api.guest_routes.generate_guest_classic_preview_session", return_value={"game_type": "build_the_word"}) as preview_mocked:
            result = launch_guest_game_preview_route(
                payload=payload,
                request=request,
                guest_session_token="guest-token",
                db=self.db,
            )
        self.assertEqual(result, {"game_type": "build_the_word"})
        preview_mocked.assert_called_once_with(self.db, "guest-token", 9, 5, "127.0.0.1")

    def test_parent_pin_routes_use_account_scope_and_session_header(self) -> None:
        with patch("backend.api.parent_pin_routes.get_parent_pin_status", return_value={"pin_enabled": False}) as status_mocked:
            result = get_parent_pin_status_route(
                current_account=self.current_account,
                parent_pin_session_token="pin-session",
                db=self.db,
            )
        self.assertEqual(result, {"pin_enabled": False})
        status_mocked.assert_called_once_with(self.db, 42, "pin-session")

        payload = ParentPinSetRequest(pin="1234")
        with patch("backend.api.parent_pin_routes.set_parent_pin", return_value={"status": "pin_set"}) as set_mocked:
            result = set_parent_pin_route(
                payload=payload,
                current_account=self.current_account,
                parent_pin_session_token="pin-session",
                db=self.db,
            )
        self.assertEqual(result, {"status": "pin_set"})
        set_mocked.assert_called_once_with(self.db, 42, "1234", "pin-session")

        verify_payload = ParentPinVerifyRequest(pin="4321")
        with patch("backend.api.parent_pin_routes.verify_parent_pin", return_value={"status": "verified"}) as verify_mocked:
            result = verify_parent_pin_route(
                payload=verify_payload,
                current_account=self.current_account,
                db=self.db,
                _=None,
            )
        self.assertEqual(result, {"status": "verified"})
        verify_mocked.assert_called_once_with(self.db, 42, "4321")

        with patch("backend.api.parent_pin_routes.clear_parent_pin_session", return_value={"status": "cleared"}) as clear_mocked:
            result = clear_parent_pin_session_route(
                current_account=self.current_account,
                parent_pin_session_token="pin-session",
                db=self.db,
            )
        self.assertEqual(result, {"status": "cleared"})
        clear_mocked.assert_called_once_with(self.db, 42, "pin-session")

    def test_parent_summary_routes_use_current_account_scope(self) -> None:
        with patch("backend.api.parent_routes.get_parent_summary", return_value={"account_id": 42}) as summary_mocked:
            result = get_parent_summary_route(current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"account_id": 42})
        summary_mocked.assert_called_once_with(self.db, 42)

        with patch("backend.api.parent_routes.get_parent_analytics", return_value={"account_id": 42}) as analytics_mocked:
            result = get_parent_analytics_route(current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"account_id": 42})
        analytics_mocked.assert_called_once_with(self.db, 42)

        with patch(
            "backend.api.parent_routes.get_parent_reader_summary",
            return_value={"reader": {"reader_id": 7}},
        ) as reader_mocked:
            result = get_parent_reader_summary_route(reader_id=7, current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"reader": {"reader_id": 7}})
        reader_mocked.assert_called_once_with(self.db, 42, 7)

    def test_reader_home_route_uses_reader_account_scope(self) -> None:
        with patch("backend.api.reader_home_routes.get_reader_home_summary", return_value={"reader": {"reader_id": 7}}) as mocked:
            result = get_reader_home_route(reader_id=7, current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"reader": {"reader_id": 7}})
        mocked.assert_called_once_with(self.db, 42, 7)

    def test_goal_routes_use_current_account_scope(self) -> None:
        with patch("backend.api.goal_routes.list_parent_goals_with_progress", return_value={"account_id": 42}) as parent_mocked:
            result = get_parent_goals_route(current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"account_id": 42})
        parent_mocked.assert_called_once_with(self.db, 42)

        create_payload = CreateGoalRequest(goal_type="stories_read", target_value=5, title="Read five stories")
        with patch("backend.api.goal_routes.create_reader_goal", return_value={"goal_id": 9}) as create_mocked:
            result = create_reader_goal_route(
                reader_id=7,
                payload=create_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"goal_id": 9})
        create_mocked.assert_called_once_with(self.db, 42, 7, "stories_read", 5, "Read five stories")

        update_payload = UpdateGoalRequest(title="Read six stories", target_value=6, is_active=False)
        with patch("backend.api.goal_routes.update_reader_goal", return_value={"goal_id": 9}) as update_mocked:
            result = update_goal_route(
                goal_id=9,
                payload=update_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"goal_id": 9})
        update_mocked.assert_called_once_with(
            self.db,
            42,
            9,
            title="Read six stories",
            target_value=6,
            is_active=False,
        )

        with patch("backend.api.goal_routes.list_reader_goals_with_progress", return_value={"reader": {"reader_id": 7}}) as reader_mocked:
            result = get_reader_goals_route(reader_id=7, current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"reader": {"reader_id": 7}})
        reader_mocked.assert_called_once_with(self.db, 42, 7)

    def test_game_foundation_routes_use_current_account_scope(self) -> None:
        deprecated_generate = generate_game_route(
            reader_id=7,
            payload=GameGenerateRequest(game_type="word_puzzle", story_id=11, difficulty_level=2, question_count=5),
            current_account=self.current_account,
            db=self.db,
        )
        self.assertEqual(deprecated_generate.status_code, 410)

        deprecated_result = record_game_result_route(
            reader_id=7,
            payload=GameResultCreateRequest(game_type="word_puzzle", difficulty_level=2, score=80, duration_seconds=45),
            current_account=self.current_account,
            db=self.db,
        )
        self.assertEqual(deprecated_result.status_code, 410)

        with patch("backend.api.game_routes.get_game_catalog", return_value={"reader_id": 7}) as catalog_mocked:
            result = get_game_catalog_route(reader_id=7, current_account=self.current_account, db=self.db)
        self.assertEqual(result, {"reader_id": 7})
        catalog_mocked.assert_called_once_with(db=self.db, account_id=42, reader_id=7)

        start_payload = GameSessionStartRequest(
            game_type="build_the_word",
            story_id=11,
            source_type="story",
            difficulty_level=2,
            item_count=8,
        )
        with patch("backend.api.game_routes.create_v1_game_session", return_value={"session_id": 9}) as create_mocked:
            result = create_game_session_route(
                reader_id=7,
                payload=start_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"session_id": 9})
        create_mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=7,
            game_type="build_the_word",
            story_id=11,
            source_type="story",
            difficulty_level=2,
            item_count=8,
        )

        with patch("backend.api.game_routes.get_v1_game_session", return_value={"session_id": 9}) as session_mocked:
            result = get_game_session_route(
                reader_id=7,
                session_id=9,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"session_id": 9})
        session_mocked.assert_called_once_with(db=self.db, account_id=42, reader_id=7, session_id=9)

        with patch("backend.api.game_routes.get_reader_game_practice_summary", return_value={"sessions_total": 3}) as summary_mocked:
            result = get_game_summary_route(
                reader_id=7,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"sessions_total": 3})
        summary_mocked.assert_called_once_with(db=self.db, account_id=42, reader_id=7)

        complete_payload = GameSessionCompleteRequest(
            completion_status="completed",
            duration_seconds=45,
            attempts=[
                {
                    "word_id": 4,
                    "word_text": "Lantern",
                    "attempt_count": 2,
                    "correct": True,
                    "time_spent_seconds": 11,
                    "hint_used": False,
                    "skipped": False,
                }
            ],
        )
        with patch("backend.api.game_routes.complete_v1_game_session", return_value={"session_id": 9}) as complete_mocked:
            result = complete_game_session_route(
                reader_id=7,
                session_id=9,
                payload=complete_payload,
                current_account=self.current_account,
                db=self.db,
            )
        self.assertEqual(result, {"session_id": 9})
        complete_mocked.assert_called_once_with(
            db=self.db,
            account_id=42,
            reader_id=7,
            session_id=9,
            completion_status="completed",
            duration_seconds=45,
            attempts=[
                {
                    "word_id": 4,
                    "word_text": "Lantern",
                    "attempt_count": 2,
                    "correct": True,
                    "time_spent_seconds": 11,
                    "hint_used": False,
                    "skipped": False,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
