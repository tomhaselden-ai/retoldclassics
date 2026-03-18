import random
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.classics.classics_semantic_search_service import discover_classics
from backend.classics.classics_repository import count_classical_stories, get_classical_story, list_classical_stories
from backend.classics.classics_serializer import (
    build_read_payload,
    build_shelf_payload,
    build_story_detail_payload,
    expand_author_filters,
    extract_preview_text,
    normalize_author,
)
from backend.games.v1_game_engine import build_v1_game_payload
from backend.guest.guest_repository import (
    GuestSessionRecord,
    count_guest_classic_reads,
    count_guest_game_launches,
    create_guest_session,
    get_guest_session_by_token,
    has_guest_classic_read,
    insert_guest_usage_event,
    touch_guest_session,
)


GUEST_ALLOWED_AUTHORS = ("Andersen", "Grimm", "Bible", "Aesop")
GUEST_CLASSIC_READ_LIMIT = 3
GUEST_GAME_LAUNCH_LIMIT = 2
GUEST_SESSION_TTL_DAYS = 7
FALLBACK_GUEST_WORDS = [
    "adventure",
    "garden",
    "wonder",
    "morning",
    "curious",
    "golden",
    "gentle",
    "forest",
]


class GuestServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_session_token(session_token: Any) -> str:
    if not isinstance(session_token, str) or not session_token.strip():
        raise GuestServiceError("guest_session_required", 401)
    return session_token.strip()


def _resolve_guest_authors(author: Any | None) -> list[str]:
    if author is None:
        return expand_author_filters(list(GUEST_ALLOWED_AUTHORS))
    if not isinstance(author, str):
        raise GuestServiceError("invalid_input", 400)
    normalized_author = normalize_author(author)
    if normalized_author not in GUEST_ALLOWED_AUTHORS:
        raise GuestServiceError("invalid_input", 400)
    return expand_author_filters([normalized_author])


def _validate_limit_offset(limit: Any, offset: Any, *, max_limit: int = 40) -> tuple[int, int]:
    if not isinstance(limit, int) or limit < 1 or limit > max_limit:
        raise GuestServiceError("invalid_input", 400)
    if not isinstance(offset, int) or offset < 0:
        raise GuestServiceError("invalid_input", 400)
    return limit, offset


def _validate_story_id(story_id: Any) -> int:
    if not isinstance(story_id, int) or story_id <= 0:
        raise GuestServiceError("invalid_identifier", 400)
    return story_id


def _validate_question_count(question_count: Any) -> int:
    if question_count is None:
        return 4
    if not isinstance(question_count, int) or question_count < 3 or question_count > 7:
        raise GuestServiceError("invalid_input", 400)
    return question_count


def _build_limits_payload(session: GuestSessionRecord, classics_reads_used: int, game_sessions_used: int) -> dict[str, Any]:
    return {
        "session_token": session.session_token,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "classics_read_limit": GUEST_CLASSIC_READ_LIMIT,
        "classics_reads_used": classics_reads_used,
        "classics_reads_remaining": max(0, GUEST_CLASSIC_READ_LIMIT - classics_reads_used),
        "game_launch_limit": GUEST_GAME_LAUNCH_LIMIT,
        "game_launches_used": game_sessions_used,
        "game_launches_remaining": max(0, GUEST_GAME_LAUNCH_LIMIT - game_sessions_used),
    }


def _load_usage_snapshot(db: Session, session: GuestSessionRecord) -> dict[str, int]:
    return {
        "classics_reads_used": count_guest_classic_reads(db, session.session_id),
        "game_launches_used": count_guest_game_launches(db, session.session_id),
    }


def _get_active_guest_session(
    db: Session,
    session_token: Any,
    client_ip: str | None,
    *,
    refresh_expiry: bool = True,
) -> GuestSessionRecord:
    normalized_token = _normalize_session_token(session_token)
    session = get_guest_session_by_token(db, normalized_token)
    if session is None:
        raise GuestServiceError("guest_session_required", 401)

    now = _utcnow()
    if session.expires_at is not None and session.expires_at.replace(tzinfo=timezone.utc) < now:
        raise GuestServiceError("guest_session_expired", 401)

    if refresh_expiry:
        touch_guest_session(
            db,
            session.session_id,
            client_ip,
            now + timedelta(days=GUEST_SESSION_TTL_DAYS),
        )
        db.commit()
        refreshed = get_guest_session_by_token(db, normalized_token)
        if refreshed is not None:
            return refreshed
    return session


def start_guest_session(db: Session, existing_session_token: Any | None = None, client_ip: str | None = None) -> dict[str, Any]:
    now = _utcnow()

    if isinstance(existing_session_token, str) and existing_session_token.strip():
        try:
            session = _get_active_guest_session(db, existing_session_token, client_ip)
            usage = _load_usage_snapshot(db, session)
            return {
                "status": "active",
                **_build_limits_payload(session, usage["classics_reads_used"], usage["game_launches_used"]),
            }
        except GuestServiceError:
            db.rollback()

    try:
        session_token = secrets.token_urlsafe(32)
        session = create_guest_session(
            db,
            session_token=session_token,
            last_ip=client_ip,
            expires_at=now + timedelta(days=GUEST_SESSION_TTL_DAYS),
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise GuestServiceError("database_failure", 500) from exc

    return {
        "status": "started",
        **_build_limits_payload(session, 0, 0),
    }


def get_guest_limits(db: Session, session_token: Any, client_ip: str | None = None) -> dict[str, Any]:
    try:
        session = _get_active_guest_session(db, session_token, client_ip)
        usage = _load_usage_snapshot(db, session)
        return _build_limits_payload(session, usage["classics_reads_used"], usage["game_launches_used"])
    except SQLAlchemyError as exc:
        db.rollback()
        raise GuestServiceError("database_failure", 500) from exc


def get_guest_classics_shelf(
    db: Session,
    author: Any | None = None,
    q: Any | None = None,
    limit: Any = 24,
    offset: Any = 0,
) -> dict[str, Any]:
    authors = _resolve_guest_authors(author)
    normalized_limit, normalized_offset = _validate_limit_offset(limit, offset, max_limit=24)
    query_text = q.strip() if isinstance(q, str) and q.strip() else None

    try:
        stories = list_classical_stories(db, authors, query_text, normalized_limit, normalized_offset)
        total_count = count_classical_stories(db, authors, query_text)
        payload = build_shelf_payload(stories, total_count)
        payload["limit"] = normalized_limit
        payload["offset"] = normalized_offset
        payload["guest_allowed_authors"] = list(GUEST_ALLOWED_AUTHORS)
        return payload
    except SQLAlchemyError as exc:
        raise GuestServiceError("database_failure", 500) from exc


def get_guest_classics_discovery(
    db: Session,
    author: Any | None = None,
    q: Any | None = None,
    limit: Any = 24,
    offset: Any = 0,
) -> dict[str, Any]:
    authors = _resolve_guest_authors(author)
    normalized_limit, normalized_offset = _validate_limit_offset(limit, offset, max_limit=24)
    query_text = q.strip() if isinstance(q, str) and q.strip() else None
    applied_author = normalize_author(author) if isinstance(author, str) and author.strip() else None

    try:
        payload = discover_classics(
            db,
            authors=authors,
            query_text=query_text,
            limit=normalized_limit,
            offset=normalized_offset,
            applied_author=applied_author,
        )
        payload["guest_allowed_authors"] = list(GUEST_ALLOWED_AUTHORS)
        return payload
    except SQLAlchemyError as exc:
        raise GuestServiceError("database_failure", 500) from exc


def get_guest_classic_story_detail(db: Session, story_id: Any) -> dict[str, Any]:
    normalized_story_id = _validate_story_id(story_id)
    try:
        story = get_classical_story(db, normalized_story_id, expand_author_filters(list(GUEST_ALLOWED_AUTHORS)))
        if story is None:
            raise GuestServiceError("story_not_found", 404)
        return build_story_detail_payload(story)
    except SQLAlchemyError as exc:
        raise GuestServiceError("database_failure", 500) from exc


def get_guest_classic_story_read(
    db: Session,
    session_token: Any,
    story_id: Any,
    client_ip: str | None = None,
) -> dict[str, Any]:
    normalized_story_id = _validate_story_id(story_id)
    session = _get_active_guest_session(db, session_token, client_ip)

    try:
        story = get_classical_story(db, normalized_story_id, expand_author_filters(list(GUEST_ALLOWED_AUTHORS)))
        if story is None:
            raise GuestServiceError("story_not_found", 404)

        if not has_guest_classic_read(db, session.session_id, normalized_story_id):
            classics_reads_used = count_guest_classic_reads(db, session.session_id)
            if classics_reads_used >= GUEST_CLASSIC_READ_LIMIT:
                raise GuestServiceError("guest_classic_limit_reached", 403)
            insert_guest_usage_event(
                db,
                session.session_id,
                "classic_read",
                story_id=normalized_story_id,
                metadata_json={"source_author": normalize_author(story.source_author)},
            )
            db.commit()

        payload = build_read_payload(story)
        payload["guest_limits"] = get_guest_limits(db, session.session_token, client_ip)
        return payload
    except GuestServiceError:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise GuestServiceError("unreadable_story", 500) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise GuestServiceError("database_failure", 500) from exc


def get_guest_games_catalog(db: Session) -> dict[str, Any]:
    shelf_payload = get_guest_classics_shelf(db, limit=6, offset=0)
    stories = [
        item
        for group in shelf_payload["groups"]
        for item in group["items"]
    ][:6]
    return {
        "game_type": "build_the_word",
        "stories": stories,
        "description": "Pick a classic and try a gentle Build the Word preview from the new game system.",
    }


def _extract_candidate_words(payload: dict[str, Any]) -> list[str]:
    text_parts: list[str] = []
    for unit in payload.get("units", []):
        if isinstance(unit, dict) and isinstance(unit.get("text"), str):
            text_parts.append(unit["text"])
    if not text_parts:
        return []

    seen: set[str] = set()
    words: list[str] = []
    for word in re.findall(r"[A-Za-z']+", " ".join(text_parts)):
        normalized = word.lower()
        if len(normalized) < 5 or not normalized.isalpha():
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        words.append(normalized)
    return words


def _build_question_choices(target: str, pool: list[str], rng: random.Random) -> list[str]:
    distractor_pool = [word for word in pool if word != target]
    distractors = rng.sample(distractor_pool, k=min(3, len(distractor_pool)))
    for fallback in FALLBACK_GUEST_WORDS:
        if len(distractors) >= 3:
            break
        if fallback != target and fallback not in distractors:
            distractors.append(fallback)
    choices = distractors + [target]
    rng.shuffle(choices)
    return [choice.title() for choice in choices]


def _extract_context_snippet(payload: dict[str, Any], target: str) -> str | None:
    for unit in payload.get("units", []):
        text = unit.get("text") if isinstance(unit, dict) else None
        if not isinstance(text, str):
            continue
        match = re.search(rf"\b{re.escape(target)}\b", text, flags=re.IGNORECASE)
        if not match:
            continue
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        return text[start:end].strip()
    return None


def _mask_target_in_context(context_text: str | None, target: str) -> str:
    if not isinstance(context_text, str) or not context_text.strip():
        return f"Find the story word: {target.title()}"
    masked = re.sub(rf"\b{re.escape(target)}\b", "_____", context_text, flags=re.IGNORECASE)
    return masked.strip() if masked.strip() else f"Find the story word: {target.title()}"


def _difficulty_for_words(words: list[str]) -> int:
    if not words:
        return 1
    average_length = sum(len(word) for word in words) / len(words)
    if average_length <= 4:
        return 1
    if average_length <= 7:
        return 2
    return 3


def generate_guest_classic_preview_session(
    db: Session,
    session_token: Any,
    story_id: Any,
    item_count: Any = None,
    client_ip: str | None = None,
) -> dict[str, Any]:
    normalized_story_id = _validate_story_id(story_id)
    normalized_item_count = _validate_question_count(item_count)
    session = _get_active_guest_session(db, session_token, client_ip)

    try:
        game_launches_used = count_guest_game_launches(db, session.session_id)
        if game_launches_used >= GUEST_GAME_LAUNCH_LIMIT:
            raise GuestServiceError("guest_game_limit_reached", 403)

        story = get_classical_story(db, normalized_story_id, expand_author_filters(list(GUEST_ALLOWED_AUTHORS)))
        if story is None:
            raise GuestServiceError("story_not_found", 404)

        read_payload = build_read_payload(story)
        candidate_words = _extract_candidate_words(read_payload)
        if len(candidate_words) < 4:
            raise GuestServiceError("missing_resource", 404)

        rng = random.Random(f"{session.session_token}:{normalized_story_id}:{game_launches_used}")
        selected_words = rng.sample(candidate_words, k=min(normalized_item_count, len(candidate_words)))
        items = []
        for index, target in enumerate(selected_words, start=1):
            context_text = _extract_context_snippet(read_payload, target)
            items.append(
                {
                    "word_id": None,
                    "word": target.title(),
                    "definition": _mask_target_in_context(context_text, target),
                    "example_sentence": context_text,
                    "difficulty_level": _difficulty_for_words([target]),
                    "reader_id": 0,
                    "story_id": normalized_story_id,
                    "source_type": "classics",
                    "trait_focus": normalize_author(story.source_author),
                    "guest_item_id": f"classic-preview-{normalized_story_id}-{index}",
                }
            )
        payload = build_v1_game_payload(
            game_type="build_the_word",
            difficulty_level=_difficulty_for_words(selected_words),
            items=items,
        )

        insert_guest_usage_event(
            db,
            session.session_id,
            "game_launch",
            story_id=normalized_story_id,
            metadata_json={"game_type": "build_the_word", "source_type": "classics"},
        )
        db.commit()

        return {
            "game_type": "build_the_word",
            "story_id": normalized_story_id,
            "story_title": story.title,
            "source_author": normalize_author(story.source_author),
            "preview_text": extract_preview_text(story),
            "payload": payload,
            "guest_limits": get_guest_limits(db, session.session_token, client_ip),
        }
    except GuestServiceError:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise GuestServiceError("unreadable_story", 500) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise GuestServiceError("database_failure", 500) from exc
