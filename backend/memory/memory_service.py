import logging
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.memory.event_repository import (
    SceneVersionRecord,
    StoryEventRecord,
    StoryVersionRecord,
    character_exists,
    get_next_scene_version_number,
    get_next_story_version_number,
    insert_scene_version,
    insert_story_event,
    insert_story_version,
    list_existing_character_ids,
    list_story_events_by_worlds,
    list_story_events_by_character,
    list_story_events_by_story,
    list_story_events_by_world,
    location_exists,
    story_belongs_to_account,
    world_exists,
)
from backend.memory.vector_index_repository import (
    get_vector_index_by_source,
    insert_vector_index,
)
from backend.worlds.world_service import get_reader_world_context_for_account


logger = logging.getLogger(__name__)

EVENT_SOURCE_TYPE = "story_event"


class MemoryServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_positive_identifier(value: int, error_code: str = "invalid_input") -> None:
    if value <= 0:
        raise MemoryServiceError(error_code=error_code, status_code=400)


def _normalize_character_ids(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise MemoryServiceError(error_code="invalid_input", status_code=400)

    normalized: list[int] = []
    for item in value:
        if not isinstance(item, int) or item <= 0:
            raise MemoryServiceError(error_code="invalid_input", status_code=400)
        normalized.append(item)
    return normalized


def _normalize_location_id(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise MemoryServiceError(error_code="invalid_input", status_code=400)
    return value


def _normalize_summary(value: Any) -> str:
    if not isinstance(value, str):
        raise MemoryServiceError(error_code="invalid_input", status_code=400)

    summary = value.strip()
    if not summary:
        raise MemoryServiceError(error_code="invalid_input", status_code=400)
    return summary


def _validate_character_references(db: Session, character_ids: list[int] | None) -> None:
    if not character_ids:
        return

    existing_ids = list_existing_character_ids(db, character_ids)
    if len(existing_ids) != len(set(character_ids)):
        raise MemoryServiceError(error_code="invalid_character_reference", status_code=404)


def _validate_location_reference(db: Session, location_id: int | None) -> None:
    if location_id is None:
        return
    if not location_exists(db, location_id):
        raise MemoryServiceError(error_code="invalid_location_reference", status_code=404)


def _serialize_story_event(event: StoryEventRecord) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "characters": event.characters,
        "location_id": event.location_id,
        "event_summary": event.event_summary,
    }


def get_story_memory(db: Session, story_id: int) -> list[dict[str, Any]]:
    _validate_positive_identifier(story_id)
    logger.info("story memory query", extra={"story_id": story_id})

    try:
        events = list_story_events_by_story(db, story_id)
    except SQLAlchemyError as exc:
        logger.exception("database failure during story memory query", extra={"story_id": story_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    if not events:
        raise MemoryServiceError(error_code="story_not_found", status_code=404)

    return [_serialize_story_event(event) for event in events]


def get_story_memory_for_account(db: Session, account_id: int, story_id: int) -> list[dict[str, Any]]:
    _validate_positive_identifier(story_id)
    logger.info("story memory query", extra={"account_id": account_id, "story_id": story_id})

    try:
        if not story_belongs_to_account(db, story_id, account_id):
            raise MemoryServiceError(error_code="story_not_found", status_code=404)
        events = list_story_events_by_story(db, story_id)
    except MemoryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during story memory query",
            extra={"account_id": account_id, "story_id": story_id},
        )
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    if not events:
        raise MemoryServiceError(error_code="story_not_found", status_code=404)

    return [_serialize_story_event(event) for event in events]


def get_character_history(db: Session, character_id: int) -> list[dict[str, Any]]:
    _validate_positive_identifier(character_id)
    logger.info("character history query", extra={"character_id": character_id})

    try:
        if not character_exists(db, character_id):
            raise MemoryServiceError(error_code="invalid_character_reference", status_code=404)

        events = list_story_events_by_character(db, character_id)
    except MemoryServiceError:
        logger.warning("character history query failed validation", extra={"character_id": character_id})
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during character history query", extra={"character_id": character_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    return [_serialize_story_event(event) for event in events]


def get_world_history(db: Session, world_id: int) -> list[dict[str, Any]]:
    _validate_positive_identifier(world_id)
    logger.info("world history query", extra={"world_id": world_id})

    try:
        if not world_exists(db, world_id):
            raise MemoryServiceError(error_code="invalid_world_reference", status_code=404)

        events = list_story_events_by_world(db, world_id)
    except MemoryServiceError:
        logger.warning("world history query failed validation", extra={"world_id": world_id})
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during world history query", extra={"world_id": world_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    return [_serialize_story_event(event) for event in events]


def get_reader_world_history(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
) -> list[dict[str, Any]]:
    _validate_positive_identifier(reader_id)
    _validate_positive_identifier(template_world_id)
    logger.info(
        "reader world history query",
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
        events = list_story_events_by_worlds(db, world_ids)
    except HTTPException as exc:
        raise MemoryServiceError(error_code="invalid_world_reference", status_code=exc.status_code) from exc
    except MemoryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world history query",
            extra={"account_id": account_id, "reader_id": reader_id, "world_id": template_world_id},
        )
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    return [_serialize_story_event(event) for event in events]


def get_reader_world_character_history(
    db: Session,
    account_id: int,
    reader_id: int,
    template_world_id: int,
    character_id: int,
) -> list[dict[str, Any]]:
    _validate_positive_identifier(reader_id)
    _validate_positive_identifier(template_world_id)
    _validate_positive_identifier(character_id, error_code="invalid_character_reference")
    logger.info(
        "reader world character history query",
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
            raise MemoryServiceError(error_code="invalid_character_reference", status_code=404)

        events = list_story_events_by_character(db, character_id)
    except HTTPException as exc:
        raise MemoryServiceError(error_code="invalid_character_reference", status_code=exc.status_code) from exc
    except MemoryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader world character history query",
            extra={
                "account_id": account_id,
                "reader_id": reader_id,
                "world_id": template_world_id,
                "character_id": character_id,
            },
        )
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    return [_serialize_story_event(event) for event in events]


def capture_story_events(
    db: Session,
    story_id: int,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    _validate_positive_identifier(story_id)
    if not isinstance(events, list):
        raise MemoryServiceError(error_code="invalid_input", status_code=400)

    logger.info(
        "event capture",
        extra={"story_id": story_id, "event_count": len(events)},
    )

    captured_events: list[dict[str, Any]] = []
    try:
        for payload in events:
            if not isinstance(payload, dict):
                raise MemoryServiceError(error_code="invalid_input", status_code=400)

            character_ids = _normalize_character_ids(payload.get("characters"))
            location_id = _normalize_location_id(payload.get("location_id"))
            event_summary = _normalize_summary(payload.get("event_summary"))

            _validate_character_references(db, character_ids)
            _validate_location_reference(db, location_id)

            event = insert_story_event(
                db=db,
                story_id=story_id,
                characters=character_ids,
                location_id=location_id,
                event_summary=event_summary,
            )

            existing_index = get_vector_index_by_source(
                db,
                source_type=EVENT_SOURCE_TYPE,
                source_id=event.event_id,
            )
            if existing_index is None:
                vector_record = insert_vector_index(
                    db=db,
                    vector_id=uuid4().hex,
                    source_type=EVENT_SOURCE_TYPE,
                    source_id=event.event_id,
                )
                vector_id = vector_record.vector_id
            else:
                vector_id = existing_index.vector_id

            captured_events.append(
                {
                    "event_id": event.event_id,
                    "story_id": event.story_id,
                    "characters": event.characters,
                    "location_id": event.location_id,
                    "event_summary": event.event_summary,
                    "vector_id": vector_id,
                }
            )

        db.commit()
    except MemoryServiceError:
        db.rollback()
        logger.warning("event capture failed validation", extra={"story_id": story_id})
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("database failure during event capture", extra={"story_id": story_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("unexpected failure during event capture", extra={"story_id": story_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc

    return captured_events


def record_story_version(
    db: Session,
    story_id: int,
    title: str | None,
    trait_focus: str | None,
    version_notes: str | None,
) -> StoryVersionRecord:
    _validate_positive_identifier(story_id)
    logger.info("story version recording", extra={"story_id": story_id})

    try:
        version_number = get_next_story_version_number(db, story_id)
        version = insert_story_version(
            db=db,
            story_id=story_id,
            version_number=version_number,
            title=title,
            trait_focus=trait_focus,
            version_notes=version_notes,
        )
        db.commit()
        return version
    except MemoryServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("database failure during story version recording", extra={"story_id": story_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("unexpected failure during story version recording", extra={"story_id": story_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc


def record_scene_version(
    db: Session,
    scene_id: int,
    scene_text: str | None,
    illustration_url: str | None,
    audio_url: str | None,
) -> SceneVersionRecord:
    _validate_positive_identifier(scene_id)
    logger.info("scene version recording", extra={"scene_id": scene_id})

    try:
        version_number = get_next_scene_version_number(db, scene_id)
        version = insert_scene_version(
            db=db,
            scene_id=scene_id,
            version_number=version_number,
            scene_text=scene_text,
            illustration_url=illustration_url,
            audio_url=audio_url,
        )
        db.commit()
        return version
    except MemoryServiceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("database failure during scene version recording", extra={"scene_id": scene_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("unexpected failure during scene version recording", extra={"scene_id": scene_id})
        raise MemoryServiceError(error_code="database_failure", status_code=500) from exc
