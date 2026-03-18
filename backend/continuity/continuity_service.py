import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.character_canon.repository import get_character_canon_profile
from backend.continuity.conflict_detector import (
    detect_character_conflicts,
    detect_story_conflicts,
    detect_world_conflicts,
)
from backend.continuity.continuity_repository import (
    get_character,
    list_character_relationships_for_character,
    list_story_events_for_character,
    list_story_events_for_story,
    list_story_events_for_world,
    list_story_events_for_worlds,
    list_world_location_names,
    list_world_rules_for_world,
    world_exists,
)
from backend.library.library_repository import get_account_reader, get_reader_library_story
from backend.reader.scene_repository import get_story_for_account
from backend.worlds.world_service import get_reader_world_context_for_account


logger = logging.getLogger(__name__)


class ContinuityServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_positive_identifier(value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ContinuityServiceError(error_code="invalid_identifier", status_code=400)


def _validate_summary(story_summary: Any) -> str:
    if not isinstance(story_summary, str):
        raise ContinuityServiceError(error_code="invalid_input", status_code=400)

    summary = story_summary.strip()
    if not summary:
        raise ContinuityServiceError(error_code="invalid_input", status_code=400)
    return summary


def _serialize_result(conflicts: list[str]) -> dict[str, Any]:
    return {
        "continuity_valid": len(conflicts) == 0,
        "conflicts": conflicts,
    }


def _append_character_canon_conflicts(story_summary: str, canon: dict[str, Any] | None, conflicts: list[str]) -> list[str]:
    if not canon:
        return conflicts

    normalized = story_summary.strip().lower()
    seen = set(conflicts)

    speech_style = str(canon.get("speech_style") or "").strip()
    if speech_style and "silent" in normalized and any(
        marker in speech_style.lower() for marker in ("talk", "chat", "express", "speaks", "voice")
    ):
        message = f"Proposed story may drift from the established speech style: {speech_style}"
        if message not in seen:
            conflicts.append(message)
            seen.add(message)

    for rule in canon.get("behavioral_rules_never") or []:
        rule_text = str(rule).strip()
        if rule_text and any(token in normalized for token in rule_text.lower().split()[:2]):
            message = f"Proposed story may violate a locked behavior rule: {rule_text}"
            if message not in seen:
                conflicts.append(message)
                seen.add(message)

    for anchor in canon.get("continuity_anchors") or []:
        anchor_text = str(anchor).strip()
        if not anchor_text:
            continue
        overlap_terms = [term for term in anchor_text.lower().split() if len(term) > 4 and term in normalized]
        if not overlap_terms:
            continue
        if any(negation in normalized for negation in ("never", "not", "no longer", "without")):
            message = f"Proposed story may contradict a continuity anchor: {anchor_text}"
            if message not in seen:
                conflicts.append(message)
                seen.add(message)

    for feature in canon.get("visual_must_never_change") or []:
        feature_text = str(feature).strip()
        if not feature_text:
            continue
        if any(negation in normalized for negation in ("missing", "different", "changed")) and any(
            token in normalized for token in feature_text.lower().split() if len(token) > 4
        ):
            message = f"Proposed story may drift from a visual lock: {feature_text}"
            if message not in seen:
                conflicts.append(message)
                seen.add(message)

    return conflicts


def evaluate_story_continuity(
    db: Session,
    story_id: int,
    world_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(story_id)
    _validate_positive_identifier(world_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "story continuity check",
        extra={"story_id": story_id, "world_id": world_id},
    )

    try:
        if not world_exists(db, world_id):
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        story_events = list_story_events_for_story(db, story_id)
        world_events = list_story_events_for_world(db, world_id)
    except ContinuityServiceError:
        logger.warning(
            "story continuity validation failed",
            extra={"story_id": story_id, "world_id": world_id},
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during story continuity check",
            extra={"story_id": story_id, "world_id": world_id},
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_story_conflicts(
        story_summary=normalized_summary,
        story_events=story_events,
        world_events=world_events,
    )
    return _serialize_result(conflicts)


def evaluate_character_continuity(
    db: Session,
    character_id: int,
    world_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(character_id)
    _validate_positive_identifier(world_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "character continuity check",
        extra={"character_id": character_id, "world_id": world_id},
    )

    try:
        if not world_exists(db, world_id):
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        character = get_character(db, character_id)
        if character is None or character.world_id != world_id:
            raise ContinuityServiceError(error_code="invalid_identifier", status_code=404)

        events = list_story_events_for_character(db, character_id)
        relationships = list_character_relationships_for_character(db, character_id)
    except ContinuityServiceError:
        logger.warning(
            "character continuity validation failed",
            extra={"character_id": character_id, "world_id": world_id},
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during character continuity check",
            extra={"character_id": character_id, "world_id": world_id},
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_character_conflicts(
        story_summary=normalized_summary,
        character=character,
        events=events,
        relationships=relationships,
    )
    return _serialize_result(conflicts)


def evaluate_world_continuity(
    db: Session,
    world_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(world_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info("world continuity check", extra={"world_id": world_id})

    try:
        if not world_exists(db, world_id):
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        world_events = list_story_events_for_world(db, world_id)
        world_rules = list_world_rules_for_world(db, world_id)
        location_names = list_world_location_names(db, world_id)
    except ContinuityServiceError:
        logger.warning("world continuity validation failed", extra={"world_id": world_id})
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during world continuity check",
            extra={"world_id": world_id},
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_world_conflicts(
        story_summary=normalized_summary,
        world_events=world_events,
        world_rules=world_rules,
        location_names=location_names,
    )
    return _serialize_result(conflicts)


def evaluate_story_continuity_for_account(
    db: Session,
    account_id: int,
    story_id: int,
    world_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(account_id)
    _validate_positive_identifier(story_id)
    _validate_positive_identifier(world_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "story continuity check",
        extra={"account_id": account_id, "story_id": story_id, "world_id": world_id},
    )

    try:
        get_story_for_account(db, story_id, account_id)
        if not world_exists(db, world_id):
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        story_events = list_story_events_for_story(db, story_id)
        world_events = list_story_events_for_world(db, world_id)
    except HTTPException as exc:
        raise ContinuityServiceError(error_code="missing_resource", status_code=exc.status_code) from exc
    except ContinuityServiceError:
        logger.warning(
            "story continuity validation failed",
            extra={"account_id": account_id, "story_id": story_id, "world_id": world_id},
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during story continuity check",
            extra={"account_id": account_id, "story_id": story_id, "world_id": world_id},
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_story_conflicts(
        story_summary=normalized_summary,
        story_events=story_events,
        world_events=world_events,
    )
    return _serialize_result(conflicts)


def evaluate_reader_world_story_continuity(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    story_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(reader_id)
    _validate_positive_identifier(template_world_id)
    _validate_positive_identifier(story_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "reader world story continuity check",
        extra={
            "account_id": account_id,
            "reader_id": reader_id,
            "world_id": template_world_id,
            "story_id": story_id,
        },
    )

    try:
        if get_account_reader(db, account_id, reader_id) is None:
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        story = get_reader_library_story(db, reader_id, story_id)
        if story is None or story.world_id != template_world_id:
            raise ContinuityServiceError(error_code="missing_resource", status_code=404)

        context = get_reader_world_context_for_account(db, account_id, reader_id, template_world_id)
        world_ids = [
            world_id
            for world_id in {
                getattr(context["template_world"], "world_id", None),
                getattr(context["derived_world"], "world_id", None),
            }
            if isinstance(world_id, int)
        ]
        story_events = list_story_events_for_story(db, story_id)
        world_events = list_story_events_for_worlds(db, world_ids)
    except HTTPException as exc:
        raise ContinuityServiceError(error_code="missing_resource", status_code=exc.status_code) from exc
    except ContinuityServiceError:
        logger.warning(
            "reader world story continuity validation failed",
            extra={
                "account_id": account_id,
                "reader_id": reader_id,
                "world_id": template_world_id,
                "story_id": story_id,
            },
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world story continuity check",
            extra={
                "account_id": account_id,
                "reader_id": reader_id,
                "world_id": template_world_id,
                "story_id": story_id,
            },
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_story_conflicts(
        story_summary=normalized_summary,
        story_events=story_events,
        world_events=world_events,
    )
    return _serialize_result(conflicts)


def evaluate_reader_world_character_continuity(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    character_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(reader_id)
    _validate_positive_identifier(template_world_id)
    _validate_positive_identifier(character_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "reader world character continuity check",
        extra={
            "account_id": account_id,
            "reader_id": reader_id,
            "world_id": template_world_id,
            "character_id": character_id,
        },
    )

    try:
        context = get_reader_world_context_for_account(db, account_id, reader_id, template_world_id)
        valid_character_ids = {
            character.character_id
            for character in context["characters"]
            if isinstance(character.character_id, int)
        }
        if character_id not in valid_character_ids:
            raise ContinuityServiceError(error_code="invalid_identifier", status_code=404)

        character = get_character(db, character_id)
        if character is None:
            raise ContinuityServiceError(error_code="invalid_identifier", status_code=404)

        events = list_story_events_for_character(db, character_id)
        relationships = list_character_relationships_for_character(db, character_id)
        canon = get_character_canon_profile(
            db,
            account_id=account_id,
            reader_world_id=context["reader_world"].reader_world_id,
            character_id=character_id,
        )
    except HTTPException as exc:
        raise ContinuityServiceError(error_code="invalid_identifier", status_code=exc.status_code) from exc
    except ContinuityServiceError:
        logger.warning(
            "reader world character continuity validation failed",
            extra={
                "account_id": account_id,
                "reader_id": reader_id,
                "world_id": template_world_id,
                "character_id": character_id,
            },
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world character continuity check",
            extra={
                "account_id": account_id,
                "reader_id": reader_id,
                "world_id": template_world_id,
                "character_id": character_id,
            },
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_character_conflicts(
        story_summary=normalized_summary,
        character=character,
        events=events,
        relationships=relationships,
    )
    conflicts = _append_character_canon_conflicts(normalized_summary, canon, conflicts)
    return _serialize_result(conflicts)


def evaluate_reader_world_continuity(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    story_summary: Any,
) -> dict[str, Any]:
    _validate_positive_identifier(reader_id)
    _validate_positive_identifier(template_world_id)
    normalized_summary = _validate_summary(story_summary)

    logger.info(
        "reader world continuity check",
        extra={"account_id": account_id, "reader_id": reader_id, "world_id": template_world_id},
    )

    try:
        context = get_reader_world_context_for_account(db, account_id, reader_id, template_world_id)
        world_ids = [
            world_id
            for world_id in {
                getattr(context["template_world"], "world_id", None),
                getattr(context["derived_world"], "world_id", None),
            }
            if isinstance(world_id, int)
        ]
        world_events = list_story_events_for_worlds(db, world_ids)
        world_rules = [rule for rule in context["world_rules"] if rule is not None]
        location_names = [
            location.name
            for location in context["locations"]
            if isinstance(location.name, str) and location.name.strip()
        ]
    except HTTPException as exc:
        raise ContinuityServiceError(error_code="missing_resource", status_code=exc.status_code) from exc
    except ContinuityServiceError:
        logger.warning(
            "reader world continuity validation failed",
            extra={"account_id": account_id, "reader_id": reader_id, "world_id": template_world_id},
        )
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world continuity check",
            extra={"account_id": account_id, "reader_id": reader_id, "world_id": template_world_id},
        )
        raise ContinuityServiceError(error_code="database_failure", status_code=500) from exc

    conflicts = detect_world_conflicts(
        story_summary=normalized_summary,
        world_events=world_events,
        world_rules=world_rules,
        location_names=location_names,
    )
    return _serialize_result(conflicts)
