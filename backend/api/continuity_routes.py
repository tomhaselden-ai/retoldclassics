from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.continuity.continuity_service import (
    ContinuityServiceError,
    evaluate_character_continuity,
    evaluate_reader_world_character_continuity,
    evaluate_reader_world_continuity,
    evaluate_reader_world_story_continuity,
    evaluate_story_continuity,
    evaluate_story_continuity_for_account,
    evaluate_world_continuity,
)
from backend.db.database import get_db


router = APIRouter(prefix="/continuity", tags=["continuity"])


class StoryContinuityRequest(BaseModel):
    story_id: int
    world_id: int
    story_summary: str


class CharacterContinuityRequest(BaseModel):
    character_id: int
    world_id: int
    story_summary: str


class WorldContinuityRequest(BaseModel):
    world_id: int
    story_summary: str


class ContinuityResponse(BaseModel):
    continuity_valid: bool
    conflicts: list[str]


def _error_response(exc: ContinuityServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code},
    )


@router.post("/story-check", response_model=ContinuityResponse)
def story_continuity_check_route(
    payload: StoryContinuityRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_story_continuity_for_account(
            db=db,
            account_id=current_account.account_id,
            story_id=payload.story_id,
            world_id=payload.world_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)


@router.post("/character-check", response_model=ContinuityResponse)
def character_continuity_check_route(
    payload: CharacterContinuityRequest,
    _: object = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_character_continuity(
            db=db,
            character_id=payload.character_id,
            world_id=payload.world_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)


@router.post("/world-check", response_model=ContinuityResponse)
def world_continuity_check_route(
    payload: WorldContinuityRequest,
    _: object = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_world_continuity(
            db=db,
            world_id=payload.world_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)


class ReaderWorldContinuityRequest(BaseModel):
    story_summary: str


@router.post("/readers/{reader_id}/worlds/{world_id}/check", response_model=ContinuityResponse)
def reader_world_continuity_check_route(
    reader_id: int,
    world_id: int,
    payload: ReaderWorldContinuityRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_reader_world_continuity(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            template_world_id=world_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)


@router.post("/readers/{reader_id}/worlds/{world_id}/characters/{character_id}/check", response_model=ContinuityResponse)
def reader_world_character_continuity_check_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    payload: ReaderWorldContinuityRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_reader_world_character_continuity(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            template_world_id=world_id,
            character_id=character_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)


@router.post("/readers/{reader_id}/worlds/{world_id}/stories/{story_id}/check", response_model=ContinuityResponse)
def reader_world_story_continuity_check_route(
    reader_id: int,
    world_id: int,
    story_id: int,
    payload: ReaderWorldContinuityRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return evaluate_reader_world_story_continuity(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            template_world_id=world_id,
            story_id=story_id,
            story_summary=payload.story_summary,
        )
    except ContinuityServiceError as exc:
        return _error_response(exc)
