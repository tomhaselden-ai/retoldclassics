from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.memory.memory_service import (
    MemoryServiceError,
    get_reader_world_character_history,
    get_reader_world_history,
    get_story_memory_for_account,
    get_character_history,
    get_world_history,
)


router = APIRouter(tags=["memory"])


class StoryMemoryEventResponse(BaseModel):
    event_id: int
    characters: list[int] | None
    location_id: int | None
    event_summary: str | None


def _error_response(exc: MemoryServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code},
    )


@router.get("/stories/{story_id}/memory", response_model=list[StoryMemoryEventResponse])
def get_story_memory_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_story_memory_for_account(db=db, account_id=current_account.account_id, story_id=story_id)
    except MemoryServiceError as exc:
        return _error_response(exc)


@router.get("/characters/{character_id}/history", response_model=list[StoryMemoryEventResponse])
def get_character_history_route(
    character_id: int,
    _: object = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_character_history(db=db, character_id=character_id)
    except MemoryServiceError as exc:
        return _error_response(exc)


@router.get("/worlds/{world_id}/history", response_model=list[StoryMemoryEventResponse])
def get_world_history_route(
    world_id: int,
    _: object = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_world_history(db=db, world_id=world_id)
    except MemoryServiceError as exc:
        return _error_response(exc)


@router.get("/readers/{reader_id}/worlds/{world_id}/history", response_model=list[StoryMemoryEventResponse])
def get_reader_world_history_route(
    reader_id: int,
    world_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_reader_world_history(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            template_world_id=world_id,
        )
    except MemoryServiceError as exc:
        return _error_response(exc)


@router.get(
    "/readers/{reader_id}/worlds/{world_id}/characters/{character_id}/history",
    response_model=list[StoryMemoryEventResponse],
)
def get_reader_world_character_history_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_reader_world_character_history(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            template_world_id=world_id,
            character_id=character_id,
        )
    except MemoryServiceError as exc:
        return _error_response(exc)
