from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.alexa.alexa_service import AlexaService, AlexaServiceError
from backend.alexa.intent_dispatcher import dispatch_alexa_request
from backend.db.database import get_db


router = APIRouter(prefix="/alexa", tags=["alexa"])


class AlexaSessionModel(BaseModel):
    session_id: str
    new: bool = False
    attributes: dict[str, Any] = Field(default_factory=dict)


class AlexaIntentModel(BaseModel):
    name: str
    slots: dict[str, Any] = Field(default_factory=dict)


class AlexaRequestModel(BaseModel):
    request_id: str
    request_type: str | None = None
    session: AlexaSessionModel | None = None
    intent: AlexaIntentModel | None = None


class AlexaSkillResponsePayload(BaseModel):
    speech_text: str
    ssml: str
    audio_url: str | None
    story_id: int | None
    scene_id: int | None
    scene_order: int | None
    end_session: bool


class AlexaSkillResponseModel(BaseModel):
    response: AlexaSkillResponsePayload
    session_attributes: dict[str, Any]


def _error_response(exc: AlexaServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
    )


@router.post("/skill", response_model=AlexaSkillResponseModel)
def alexa_skill_route(
    payload: AlexaRequestModel,
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    service = AlexaService()
    try:
        return dispatch_alexa_request(
            service=service,
            db=db,
            request_type=payload.request_type,
            intent=payload.intent.model_dump() if payload.intent is not None else None,
            session_attributes=payload.session.attributes if payload.session is not None else {},
        )
    except AlexaServiceError as exc:
        return _error_response(exc)
