import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.scaling.scaling_repository import (
    count_account_assigned_worlds,
    count_account_generated_stories,
    count_account_index_rows,
    count_account_indexed_story_events,
    count_account_readers,
    count_account_story_events,
    count_default_worlds,
    count_worlds,
    get_account,
    get_account_reader,
    list_reader_world_assignments,
    list_worlds,
)


logger = logging.getLogger(__name__)


class ScalingServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_identifier(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ScalingServiceError(error_code="invalid_identifier", status_code=400)
    return value


def _validate_limit_offset(limit: Any, offset: Any) -> tuple[int, int]:
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ScalingServiceError(error_code="invalid_input", status_code=400)
    if not isinstance(offset, int) or offset < 0:
        raise ScalingServiceError(error_code="invalid_input", status_code=400)
    return limit, offset


def _is_subscription_premium(subscription_level: str | None) -> bool:
    if not subscription_level:
        return False
    return subscription_level.strip().lower() not in {"free", ""}


def get_universe_summary(
    db: Session,
    requesting_account_id: int,
    account_id: Any,
) -> dict[str, Any]:
    normalized_account_id = _validate_identifier(account_id)
    if normalized_account_id != requesting_account_id:
        raise ScalingServiceError(error_code="forbidden", status_code=403)

    logger.info("universe summary requested", extra={"account_id": normalized_account_id})

    try:
        account = get_account(db, normalized_account_id)
        if account is None:
            raise ScalingServiceError(error_code="account_not_found", status_code=404)

        return {
            "account_id": account.account_id,
            "subscription_level": account.subscription_level,
            "story_security": account.story_security,
            "reader_count": count_account_readers(db, account.account_id),
            "assigned_world_count": count_account_assigned_worlds(db, account.account_id),
            "generated_story_count": count_account_generated_stories(db, account.account_id),
            "available_world_count": count_worlds(db) if _is_subscription_premium(account.subscription_level) else count_default_worlds(db),
            "indexed_memory_count": count_account_index_rows(db, account.account_id),
        }
    except ScalingServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during universe summary", extra={"account_id": normalized_account_id})
        raise ScalingServiceError(error_code="database_failure", status_code=500) from exc


def get_reader_world_access(
    db: Session,
    account_id: int,
    reader_id: Any,
) -> dict[str, Any]:
    normalized_reader_id = _validate_identifier(reader_id)
    logger.info("reader world access requested", extra={"account_id": account_id, "reader_id": normalized_reader_id})

    try:
        account = get_account(db, account_id)
        if account is None:
            raise ScalingServiceError(error_code="account_not_found", status_code=404)

        reader = get_account_reader(db, account_id, normalized_reader_id)
        if reader is None:
            raise ScalingServiceError(error_code="reader_not_found", status_code=404)

        assignments = list_reader_world_assignments(db, normalized_reader_id)
        available_default_only = not _is_subscription_premium(account.subscription_level)

        return {
            "reader_id": reader.reader_id,
            "reader_name": reader.name,
            "subscription_level": account.subscription_level,
            "world_access_policy": "default_worlds_only" if available_default_only else "all_worlds",
            "assigned_world_count": len(assignments),
            "assigned_worlds": [
                {
                    "reader_world_id": item.reader_world_id,
                    "world_id": item.world_id,
                    "world_name": item.world_name,
                    "custom_name": item.custom_name,
                    "default_world": item.world_default_world,
                    "created_at": item.created_at,
                }
                for item in assignments
            ],
        }
    except ScalingServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world access lookup",
            extra={"account_id": account_id, "reader_id": normalized_reader_id},
        )
        raise ScalingServiceError(error_code="database_failure", status_code=500) from exc


def get_available_worlds(
    db: Session,
    requesting_account_id: int,
    account_id: Any,
    reader_id: Any | None,
    limit: Any,
    offset: Any,
) -> dict[str, Any]:
    normalized_account_id = _validate_identifier(account_id)
    if normalized_account_id != requesting_account_id:
        raise ScalingServiceError(error_code="forbidden", status_code=403)
    normalized_limit, normalized_offset = _validate_limit_offset(limit, offset)

    logger.info(
        "available worlds requested",
        extra={"account_id": normalized_account_id, "reader_id": reader_id, "limit": normalized_limit, "offset": normalized_offset},
    )

    try:
        account = get_account(db, normalized_account_id)
        if account is None:
            raise ScalingServiceError(error_code="account_not_found", status_code=404)

        resolved_reader_id: int | None = None
        assigned_world_ids: set[int] = set()
        if reader_id is not None:
            resolved_reader_id = _validate_identifier(reader_id)
            reader = get_account_reader(db, normalized_account_id, resolved_reader_id)
            if reader is None:
                raise ScalingServiceError(error_code="reader_not_found", status_code=404)
            assigned_world_ids = {
                item.world_id for item in list_reader_world_assignments(db, resolved_reader_id) if item.world_id is not None
            }

        premium = _is_subscription_premium(account.subscription_level)
        worlds = list_worlds(db, normalized_limit, normalized_offset)
        if not premium:
            worlds = [world for world in worlds if world.default_world]

        return {
            "account_id": normalized_account_id,
            "reader_id": resolved_reader_id,
            "subscription_level": account.subscription_level,
            "world_access_policy": "all_worlds" if premium else "default_worlds_only",
            "limit": normalized_limit,
            "offset": normalized_offset,
            "worlds": [
                {
                    "world_id": world.world_id,
                    "name": world.name,
                    "description": world.description,
                    "default_world": world.default_world,
                    "updated_at": world.updated_at,
                    "assigned_to_reader": world.world_id in assigned_world_ids,
                }
                for world in worlds
            ],
        }
    except ScalingServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during available worlds lookup", extra={"account_id": normalized_account_id})
        raise ScalingServiceError(error_code="database_failure", status_code=500) from exc


def get_memory_index_health(
    db: Session,
    requesting_account_id: int,
    account_id: Any,
) -> dict[str, Any]:
    normalized_account_id = _validate_identifier(account_id)
    if normalized_account_id != requesting_account_id:
        raise ScalingServiceError(error_code="forbidden", status_code=403)

    logger.info("memory index health requested", extra={"account_id": normalized_account_id})

    try:
        account = get_account(db, normalized_account_id)
        if account is None:
            raise ScalingServiceError(error_code="account_not_found", status_code=404)

        total_story_events = count_account_story_events(db, normalized_account_id)
        indexed_story_events = count_account_indexed_story_events(db, normalized_account_id)
        pending_story_events = max(0, total_story_events - indexed_story_events)
        coverage_ratio = 1.0 if total_story_events == 0 else round(indexed_story_events / total_story_events, 4)

        return {
            "account_id": normalized_account_id,
            "total_story_events": total_story_events,
            "indexed_story_events": indexed_story_events,
            "pending_story_events": pending_story_events,
            "coverage_ratio": coverage_ratio,
            "status": "healthy" if pending_story_events == 0 else "attention_required",
        }
    except ScalingServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during memory index health lookup", extra={"account_id": normalized_account_id})
        raise ScalingServiceError(error_code="database_failure", status_code=500) from exc
