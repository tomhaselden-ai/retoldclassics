from typing import Any

from sqlalchemy.orm import Session

from backend.alexa.alexa_service import AlexaService, AlexaServiceError, _normalize_session_attributes, _normalize_slots


def dispatch_alexa_request(
    service: AlexaService,
    db: Session,
    request_type: str | None,
    intent: dict[str, Any] | None,
    session_attributes: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_session_attributes = _normalize_session_attributes(session_attributes)

    if request_type == "LaunchRequest" and intent is None:
        return service.handle_request(
            db=db,
            intent_name="LaunchRequest",
            slots={},
            session_attributes=normalized_session_attributes,
        )

    if not isinstance(intent, dict):
        raise AlexaServiceError(
            error_code="invalid_request",
            status_code=400,
            message="Intent payload is required.",
        )

    intent_name = intent.get("name")
    if not isinstance(intent_name, str) or not intent_name.strip():
        raise AlexaServiceError(
            error_code="invalid_request",
            status_code=400,
            message="Intent name is required.",
        )

    slots = _normalize_slots(intent.get("slots"))
    return service.handle_request(
        db=db,
        intent_name=intent_name.strip(),
        slots=slots,
        session_attributes=normalized_session_attributes,
    )
