import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.alexa.alexa_repository import (
    get_character_by_name,
    get_character_by_species,
    get_latest_reader_world,
    get_latest_story_for_reader,
    get_location,
    get_narration_for_scene,
    get_reader,
    get_reader_world_by_id,
    get_reader_world_by_world_id,
    get_story_for_reader,
    get_story_scene_by_order,
    get_world_by_name,
    list_story_events_for_character,
)
from backend.alexa.response_builder import build_alexa_response
from backend.reader.scene_repository import extract_scene_text
from backend.story_engine.story_engine import generate_story_for_reader


logger = logging.getLogger(__name__)

DEFAULT_THEME = "bedtime"
DEFAULT_TARGET_LENGTH = "short"


class AlexaServiceError(Exception):
    def __init__(self, error_code: str, status_code: int, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.message = message


def _coerce_positive_int(value: Any, error_code: str, message: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        if parsed > 0:
            return parsed
    raise AlexaServiceError(error_code=error_code, status_code=400, message=message)


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return str(value).strip() or None


def _normalize_slots(slots: Any) -> dict[str, Any]:
    if slots is None:
        return {}
    if not isinstance(slots, dict):
        raise AlexaServiceError(
            error_code="invalid_request",
            status_code=400,
            message="Intent slots must be an object.",
        )
    return slots


def _normalize_session_attributes(attributes: Any) -> dict[str, Any]:
    if attributes is None:
        return {}
    if not isinstance(attributes, dict):
        raise AlexaServiceError(
            error_code="invalid_request",
            status_code=400,
            message="Session attributes must be an object.",
        )
    return attributes


def _normalize_personality_traits(value: Any) -> str | None:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        if parts:
            return ", ".join(parts)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _resolve_reader(reader_id: Any, db: Session):
    normalized_reader_id = _coerce_positive_int(
        reader_id,
        error_code="invalid_request",
        message="reader_id must be a positive integer.",
    )
    if normalized_reader_id is None:
        raise AlexaServiceError(
            error_code="invalid_request",
            status_code=400,
            message="reader_id is required.",
        )

    reader = get_reader(db, normalized_reader_id)
    if reader is None:
        raise AlexaServiceError(
            error_code="reader_not_found",
            status_code=404,
            message="The supplied reader_id does not exist.",
        )
    return reader


def _resolve_reader_world(
    db: Session,
    reader_id: int,
    slots: dict[str, Any],
    session_attributes: dict[str, Any],
):
    reader_world_id = _coerce_positive_int(
        slots.get("reader_world_id", session_attributes.get("reader_world_id")),
        error_code="invalid_request",
        message="reader_world_id must be a positive integer.",
    )
    world_id = _coerce_positive_int(
        slots.get("world_id"),
        error_code="invalid_request",
        message="world_id must be a positive integer.",
    )
    world_name = _coerce_string(slots.get("world_name"))

    reader_world = None
    if reader_world_id is not None:
        reader_world = get_reader_world_by_id(db, reader_id, reader_world_id)
    elif world_id is not None:
        reader_world = get_reader_world_by_world_id(db, reader_id, world_id)
    elif world_name:
        world = get_world_by_name(db, world_name)
        if world is not None:
            reader_world = get_reader_world_by_world_id(db, reader_id, world.world_id)
    else:
        reader_world = get_latest_reader_world(db, reader_id)

    if reader_world is None or reader_world.world_id is None:
        raise AlexaServiceError(
            error_code="world_not_found",
            status_code=404,
            message="The supplied reader_world_id or world could not be resolved.",
        )
    return reader_world


def _serialize_scene_response(scene, narration) -> tuple[str, str | None]:
    scene_text = extract_scene_text(scene.scene_text)
    audio_url = narration.audio_url if narration is not None else None
    return scene_text, audio_url


class AlexaService:
    def handle_launch(self, session_attributes: dict[str, Any]) -> dict[str, Any]:
        logger.info("alexa launch request")
        return build_alexa_response(
            "Welcome back. You can say tell me a bedtime story, continue my adventure, or ask who a character is.",
            session_attributes=session_attributes,
        )

    def start_story(self, db: Session, slots: dict[str, Any], session_attributes: dict[str, Any]) -> dict[str, Any]:
        reader = _resolve_reader(slots.get("reader_id", session_attributes.get("reader_id")), db)
        reader_world = _resolve_reader_world(db, reader.reader_id, slots, session_attributes)

        theme = _coerce_string(slots.get("theme")) or DEFAULT_THEME
        target_length = _coerce_string(slots.get("target_length")) or DEFAULT_TARGET_LENGTH

        logger.info(
            "alexa start story request",
            extra={"reader_id": reader.reader_id, "reader_world_id": reader_world.reader_world_id},
        )

        story_payload = generate_story_for_reader(
            db=db,
            account_id=reader.account_id,
            reader_id=reader.reader_id,
            world_id=reader_world.world_id,
            theme=theme,
            target_length=target_length,
        )

        story = get_story_for_reader(db, reader.reader_id, story_payload["story_id"])
        if story is None:
            raise AlexaServiceError(
                error_code="story_not_found",
                status_code=404,
                message="No generated story could be resolved for the request.",
            )

        first_scene = get_story_scene_by_order(db, story.story_id, 1)
        if first_scene is None:
            raise AlexaServiceError(
                error_code="scene_not_found",
                status_code=404,
                message="No scene could be resolved for the selected story.",
            )

        narration = get_narration_for_scene(db, story.story_id, first_scene.scene_id)
        speech_text, audio_url = _serialize_scene_response(first_scene, narration)

        next_session_attributes = dict(session_attributes)
        next_session_attributes.update(
            {
                "reader_id": reader.reader_id,
                "reader_world_id": reader_world.reader_world_id,
                "story_id": story.story_id,
                "scene_order": first_scene.scene_order,
            }
        )
        return build_alexa_response(
            speech_text,
            audio_url=audio_url,
            story_id=story.story_id,
            scene_id=first_scene.scene_id,
            scene_order=first_scene.scene_order,
            session_attributes=next_session_attributes,
        )

    def continue_adventure(self, db: Session, slots: dict[str, Any], session_attributes: dict[str, Any]) -> dict[str, Any]:
        reader = _resolve_reader(slots.get("reader_id", session_attributes.get("reader_id")), db)

        story_id = _coerce_positive_int(
            slots.get("story_id", session_attributes.get("story_id")),
            error_code="invalid_request",
            message="story_id must be a positive integer.",
        )
        reader_world_id = _coerce_positive_int(
            session_attributes.get("reader_world_id"),
            error_code="invalid_request",
            message="reader_world_id must be a positive integer.",
        )

        if story_id is not None:
            story = get_story_for_reader(db, reader.reader_id, story_id)
        else:
            story = get_latest_story_for_reader(db, reader.reader_id, reader_world_id=reader_world_id)
            if story is None:
                story = get_latest_story_for_reader(db, reader.reader_id)

        if story is None:
            raise AlexaServiceError(
                error_code="story_not_found",
                status_code=404,
                message="No generated story could be resolved for the request.",
            )

        requested_scene_order = _coerce_positive_int(
            slots.get("scene_order"),
            error_code="invalid_request",
            message="scene_order must be a positive integer.",
        )
        current_scene_order = _coerce_positive_int(
            session_attributes.get("scene_order"),
            error_code="invalid_request",
            message="scene_order must be a positive integer.",
        )

        if requested_scene_order is not None:
            target_scene_order = requested_scene_order
        elif current_scene_order is not None:
            target_scene_order = current_scene_order + 1
        else:
            target_scene_order = 1

        scene = get_story_scene_by_order(db, story.story_id, target_scene_order)
        if scene is None:
            return build_alexa_response(
                "That adventure has reached the end. You can ask me for a new bedtime story whenever you are ready.",
                story_id=story.story_id,
                session_attributes={
                    "reader_id": reader.reader_id,
                    "reader_world_id": story.reader_world_id,
                    "story_id": story.story_id,
                    "scene_order": current_scene_order,
                },
            )

        narration = get_narration_for_scene(db, story.story_id, scene.scene_id)
        speech_text, audio_url = _serialize_scene_response(scene, narration)

        next_session_attributes = dict(session_attributes)
        next_session_attributes.update(
            {
                "reader_id": reader.reader_id,
                "reader_world_id": story.reader_world_id,
                "story_id": story.story_id,
                "scene_order": scene.scene_order,
            }
        )
        return build_alexa_response(
            speech_text,
            audio_url=audio_url,
            story_id=story.story_id,
            scene_id=scene.scene_id,
            scene_order=scene.scene_order,
            session_attributes=next_session_attributes,
        )

    def answer_character_question(
        self,
        db: Session,
        slots: dict[str, Any],
        session_attributes: dict[str, Any],
    ) -> dict[str, Any]:
        reader = _resolve_reader(slots.get("reader_id", session_attributes.get("reader_id")), db)
        character_name = _coerce_string(slots.get("character_name"))
        if not character_name:
            raise AlexaServiceError(
                error_code="invalid_request",
                status_code=400,
                message="character_name is required for CharacterQuestionIntent.",
            )

        reader_world = _resolve_reader_world(db, reader.reader_id, slots, session_attributes)

        character = get_character_by_name(db, reader_world.world_id, character_name)
        if character is None:
            character = get_character_by_species(db, reader_world.world_id, character_name)
        if character is None:
            raise AlexaServiceError(
                error_code="character_not_found",
                status_code=404,
                message="The requested character could not be resolved in the active world.",
            )

        traits = _normalize_personality_traits(character.personality_traits)
        home_location = get_location(db, character.home_location) if character.home_location is not None else None
        recent_events = list_story_events_for_character(db, character.character_id, limit=2)

        parts = []
        if character.name and character.species:
            parts.append(f"{character.name} is a {character.species} in this world.")
        elif character.name:
            parts.append(f"{character.name} is an important character in this world.")

        if traits:
            parts.append(f"{character.name or 'This character'} is known for being {traits}.")

        if home_location is not None and home_location.name:
            parts.append(f"{character.name or 'They'} is often connected to {home_location.name}.")

        if recent_events:
            latest_summary = recent_events[0].event_summary
            if latest_summary:
                parts.append(f"Recently, {latest_summary}.")

        speech_text = " ".join(parts).strip()
        if not speech_text:
            speech_text = "I found that character, but I do not have enough detail to describe them yet."

        next_session_attributes = dict(session_attributes)
        next_session_attributes.update(
            {
                "reader_id": reader.reader_id,
                "reader_world_id": reader_world.reader_world_id,
            }
        )
        return build_alexa_response(
            speech_text,
            story_id=_coerce_positive_int(
                slots.get("story_id", session_attributes.get("story_id")),
                error_code="invalid_request",
                message="story_id must be a positive integer.",
            ),
            session_attributes=next_session_attributes,
        )

    def handle_request(self, db: Session, intent_name: str, slots: dict[str, Any], session_attributes: dict[str, Any]) -> dict[str, Any]:
        try:
            if intent_name == "LaunchRequest":
                return self.handle_launch(session_attributes)
            if intent_name == "StartStoryIntent":
                return self.start_story(db, slots, session_attributes)
            if intent_name == "ContinueAdventureIntent":
                return self.continue_adventure(db, slots, session_attributes)
            if intent_name == "CharacterQuestionIntent":
                return self.answer_character_question(db, slots, session_attributes)
        except AlexaServiceError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("database failure during alexa request", extra={"intent_name": intent_name})
            raise AlexaServiceError(
                error_code="database_failure",
                status_code=500,
                message="A database operation failed.",
            ) from exc

        raise AlexaServiceError(
            error_code="invalid_intent",
            status_code=400,
            message="Unsupported Alexa intent.",
        )
