from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.safety.safety_service import (
    SafetyServiceError,
    get_scene_safety_report,
    get_story_safety_report,
    validate_text_content,
)


router = APIRouter(tags=["safety"])


class TextSafetyRequest(BaseModel):
    text: str = Field(min_length=1)


class SafetyEvaluationResponse(BaseModel):
    safety_score: int
    classification: str
    flags: list[str]
    matched_terms: list[str]
    account_story_security: str | None = None


class StorySceneSafetyResponse(SafetyEvaluationResponse):
    scene_id: int
    scene_order: int | None
    scene_text: str


class StoryEventSafetyResponse(SafetyEvaluationResponse):
    event_id: int
    event_summary: str


class StorySafetyReportResponse(BaseModel):
    story_id: int
    title: str | None
    account_story_security: str | None
    classification: str
    safety_score: int
    flags: list[str]
    matched_terms: list[str]
    scenes: list[StorySceneSafetyResponse]
    events: list[StoryEventSafetyResponse]


class SceneSafetyReportResponse(SafetyEvaluationResponse):
    story_id: int
    scene_id: int
    scene_order: int | None
    scene_text: str


def _error_response(exc: SafetyServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
    )


@router.post("/safety/text-check", response_model=SafetyEvaluationResponse)
def text_safety_check_route(
    payload: TextSafetyRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return validate_text_content(db, current_account.account_id, payload.text)
    except SafetyServiceError as exc:
        return _error_response(exc)


@router.get("/stories/{story_id}/safety-report", response_model=StorySafetyReportResponse)
def story_safety_report_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_story_safety_report(db, current_account.account_id, story_id)
    except SafetyServiceError as exc:
        return _error_response(exc)


@router.get("/stories/{story_id}/scenes/{scene_id}/safety-report", response_model=SceneSafetyReportResponse)
def scene_safety_report_route(
    story_id: int,
    scene_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_scene_safety_report(db, current_account.account_id, story_id, scene_id)
    except SafetyServiceError as exc:
        return _error_response(exc)
