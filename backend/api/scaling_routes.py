from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.scaling.scaling_service import (
    ScalingServiceError,
    get_available_worlds,
    get_memory_index_health,
    get_reader_world_access,
    get_universe_summary,
)


router = APIRouter(tags=["scaling"])


class UniverseSummaryResponse(BaseModel):
    account_id: int
    subscription_level: str | None
    story_security: str | None
    reader_count: int
    assigned_world_count: int
    generated_story_count: int
    available_world_count: int
    indexed_memory_count: int


class AssignedWorldResponse(BaseModel):
    reader_world_id: int
    world_id: int | None
    world_name: str | None
    custom_name: str | None
    default_world: bool | None
    created_at: datetime | None


class ReaderWorldAccessResponse(BaseModel):
    reader_id: int
    reader_name: str | None
    subscription_level: str | None
    world_access_policy: str
    assigned_world_count: int
    assigned_worlds: list[AssignedWorldResponse]


class AvailableWorldResponse(BaseModel):
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None
    updated_at: datetime | None
    assigned_to_reader: bool


class AvailableWorldsResponse(BaseModel):
    account_id: int
    reader_id: int | None
    subscription_level: str | None
    world_access_policy: str
    limit: int
    offset: int
    worlds: list[AvailableWorldResponse]


class MemoryIndexHealthResponse(BaseModel):
    account_id: int
    total_story_events: int
    indexed_story_events: int
    pending_story_events: int
    coverage_ratio: float
    status: str


def _error_response(exc: ScalingServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/accounts/{account_id}/universe-summary", response_model=UniverseSummaryResponse)
def get_universe_summary_route(
    account_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_universe_summary(db, current_account.account_id, account_id)
    except ScalingServiceError as exc:
        return _error_response(exc)


@router.get("/readers/{reader_id}/world-access", response_model=ReaderWorldAccessResponse)
def get_reader_world_access_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_reader_world_access(db, current_account.account_id, reader_id)
    except ScalingServiceError as exc:
        return _error_response(exc)


@router.get("/accounts/{account_id}/worlds/available", response_model=AvailableWorldsResponse)
def get_available_worlds_route(
    account_id: int,
    reader_id: int | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_available_worlds(
            db,
            current_account.account_id,
            account_id,
            reader_id,
            limit,
            offset,
        )
    except ScalingServiceError as exc:
        return _error_response(exc)


@router.get("/accounts/{account_id}/memory/index-health", response_model=MemoryIndexHealthResponse)
def get_memory_index_health_route(
    account_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_memory_index_health(db, current_account.account_id, account_id)
    except ScalingServiceError as exc:
        return _error_response(exc)
