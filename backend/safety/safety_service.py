import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.reader.scene_repository import extract_scene_text
from backend.safety.safety_repository import (
    get_account_policy,
    get_story_for_account,
    get_story_scene,
    list_story_events,
    list_story_scenes,
)
from backend.safety.safety_rules import SafetyEvaluation, evaluate_text_safety


logger = logging.getLogger(__name__)


class SafetyServiceError(Exception):
    def __init__(self, error_code: str, status_code: int, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.message = message


def _validate_positive_identifier(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value <= 0:
        raise SafetyServiceError(
            error_code="invalid_input",
            status_code=400,
            message=f"{field_name} must be a positive integer.",
        )


def _validate_text(value: Any) -> str:
    if not isinstance(value, str):
        raise SafetyServiceError(
            error_code="invalid_input",
            status_code=400,
            message="text must be a non-empty string.",
        )
    normalized = value.strip()
    if not normalized:
        raise SafetyServiceError(
            error_code="invalid_input",
            status_code=400,
            message="text must be a non-empty string.",
        )
    return normalized


def _serialize_evaluation(evaluation: SafetyEvaluation, account_story_security: str | None = None) -> dict[str, Any]:
    payload = {
        "safety_score": evaluation.safety_score,
        "classification": evaluation.classification,
        "flags": evaluation.flags,
        "matched_terms": evaluation.matched_terms,
    }
    if account_story_security is not None:
        payload["account_story_security"] = account_story_security
    return payload


def validate_text_content(db: Session, account_id: int, text: Any) -> dict[str, Any]:
    normalized_text = _validate_text(text)
    logger.info("safety text check", extra={"account_id": account_id})

    try:
        account_policy = get_account_policy(db, account_id)
    except SQLAlchemyError as exc:
        logger.exception("database failure during safety text check", extra={"account_id": account_id})
        raise SafetyServiceError(
            error_code="database_failure",
            status_code=500,
            message="A database operation failed.",
        ) from exc

    evaluation = evaluate_text_safety(normalized_text)
    return _serialize_evaluation(
        evaluation,
        account_story_security=account_policy.story_security if account_policy is not None else None,
    )


def get_story_safety_report(db: Session, account_id: int, story_id: int) -> dict[str, Any]:
    _validate_positive_identifier(story_id, "story_id")
    logger.info("story safety report requested", extra={"account_id": account_id, "story_id": story_id})

    try:
        account_policy = get_account_policy(db, account_id)
        story = get_story_for_account(db, account_id, story_id)
        scenes = list_story_scenes(db, story.story_id)
        events = list_story_events(db, story.story_id)
    except HTTPException as exc:
        if exc.status_code == 404:
            raise SafetyServiceError(
                error_code="story_not_found",
                status_code=404,
                message="Story not found.",
            ) from exc
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during story safety report", extra={"story_id": story_id})
        raise SafetyServiceError(
            error_code="database_failure",
            status_code=500,
            message="A database operation failed.",
        ) from exc

    scene_reports: list[dict[str, Any]] = []
    story_flags: set[str] = set()
    story_terms: set[str] = set()
    classifications: list[str] = []

    for scene in scenes:
        scene_text = extract_scene_text(scene.scene_text)
        evaluation = evaluate_text_safety(scene_text)
        classifications.append(evaluation.classification)
        story_flags.update(evaluation.flags)
        story_terms.update(evaluation.matched_terms)
        scene_reports.append(
            {
                "scene_id": scene.scene_id,
                "scene_order": scene.scene_order,
                "scene_text": scene_text,
                **_serialize_evaluation(evaluation),
            }
        )

    event_reports: list[dict[str, Any]] = []
    for event in events:
        event_text = (event.event_summary or "").strip()
        if not event_text:
            continue
        evaluation = evaluate_text_safety(event_text)
        classifications.append(evaluation.classification)
        story_flags.update(evaluation.flags)
        story_terms.update(evaluation.matched_terms)
        event_reports.append(
            {
                "event_id": event.event_id,
                "event_summary": event_text,
                **_serialize_evaluation(evaluation),
            }
        )

    if "blocked" in classifications:
        overall = "blocked"
    elif "review_required" in classifications:
        overall = "review_required"
    else:
        overall = "approved"

    lowest_score = 100
    for item in scene_reports:
        lowest_score = min(lowest_score, item["safety_score"])
    for item in event_reports:
        lowest_score = min(lowest_score, item["safety_score"])

    return {
        "story_id": story.story_id,
        "title": story.title,
        "account_story_security": account_policy.story_security if account_policy is not None else None,
        "classification": overall,
        "safety_score": lowest_score,
        "flags": sorted(story_flags),
        "matched_terms": sorted(story_terms),
        "scenes": scene_reports,
        "events": event_reports,
    }


def get_scene_safety_report(db: Session, account_id: int, story_id: int, scene_id: int) -> dict[str, Any]:
    _validate_positive_identifier(story_id, "story_id")
    _validate_positive_identifier(scene_id, "scene_id")
    logger.info(
        "scene safety report requested",
        extra={"account_id": account_id, "story_id": story_id, "scene_id": scene_id},
    )

    try:
        account_policy = get_account_policy(db, account_id)
        story = get_story_for_account(db, account_id, story_id)
        scene = get_story_scene(db, story.story_id, scene_id)
    except HTTPException as exc:
        if exc.status_code == 404:
            raise SafetyServiceError(
                error_code="scene_not_found",
                status_code=404,
                message="Scene not found.",
            ) from exc
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during scene safety report", extra={"story_id": story_id, "scene_id": scene_id})
        raise SafetyServiceError(
            error_code="database_failure",
            status_code=500,
            message="A database operation failed.",
        ) from exc

    scene_text = extract_scene_text(scene.scene_text)
    evaluation = evaluate_text_safety(scene_text)
    return {
        "story_id": story.story_id,
        "scene_id": scene.scene_id,
        "scene_order": scene.scene_order,
        "scene_text": scene_text,
        **_serialize_evaluation(
            evaluation,
            account_story_security=account_policy.story_security if account_policy is not None else None,
        ),
    }
