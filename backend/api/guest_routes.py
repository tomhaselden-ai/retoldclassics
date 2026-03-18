from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.guest.guest_service import (
    GuestServiceError,
    generate_guest_classic_preview_session,
    get_guest_classic_story_detail,
    get_guest_classic_story_read,
    get_guest_classics_discovery,
    get_guest_classics_shelf,
    get_guest_games_catalog,
    get_guest_limits,
    start_guest_session,
)


router = APIRouter(prefix="/guest", tags=["guest"])


class GuestSessionStartRequest(BaseModel):
    existing_session_token: str | None = None


class GuestLimitsResponse(BaseModel):
    session_token: str
    expires_at: str | None
    classics_read_limit: int
    classics_reads_used: int
    classics_reads_remaining: int
    game_launch_limit: int
    game_launches_used: int
    game_launches_remaining: int


class GuestSessionStartResponse(GuestLimitsResponse):
    status: str


class GuestGameStoryResponse(BaseModel):
    story_id: int
    title: str | None
    source_author: str | None
    age_range: str | None
    reading_level: str | None
    preview_text: str
    cover: dict[str, Any]
    immersive_reader_available: bool


class GuestGamesCatalogResponse(BaseModel):
    game_type: str
    description: str
    stories: list[GuestGameStoryResponse]


class GuestGameLaunchRequest(BaseModel):
    story_id: int = Field(ge=1)
    item_count: int | None = Field(default=None, ge=3, le=7)


class GuestGameLaunchResponse(BaseModel):
    game_type: str
    story_id: int
    story_title: str | None
    source_author: str | None
    preview_text: str
    payload: dict[str, Any]
    guest_limits: GuestLimitsResponse


def _error_response(exc: GuestServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/session/start", response_model=GuestSessionStartResponse)
def start_guest_session_route(
    payload: GuestSessionStartRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return start_guest_session(db, payload.existing_session_token, _client_ip(request))
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/limits", response_model=GuestLimitsResponse)
def get_guest_limits_route(
    request: Request,
    guest_session_token: str | None = Header(default=None, alias="X-Guest-Session"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_guest_limits(db, guest_session_token, _client_ip(request))
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/classics", response_model=None)
def get_guest_classics_route(
    author: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=24),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_guest_classics_shelf(db, author=author, q=q, limit=limit, offset=offset)
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/classics/discover", response_model=None)
def get_guest_classics_discovery_route(
    author: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=24),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return get_guest_classics_discovery(db, author=author, q=q, limit=limit, offset=offset)
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/classics/stories/{story_id}", response_model=None)
def get_guest_classic_story_detail_route(
    story_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_guest_classic_story_detail(db, story_id)
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/classics/stories/{story_id}/read", response_model=None)
def get_guest_classic_story_read_route(
    story_id: int,
    request: Request,
    guest_session_token: str | None = Header(default=None, alias="X-Guest-Session"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_guest_classic_story_read(db, guest_session_token, story_id, _client_ip(request))
    except GuestServiceError as exc:
        return _error_response(exc)


@router.get("/games", response_model=GuestGamesCatalogResponse)
def get_guest_games_catalog_route(db: Session = Depends(get_db)) -> dict[str, Any] | JSONResponse:
    try:
        return get_guest_games_catalog(db)
    except GuestServiceError as exc:
        return _error_response(exc)


@router.post("/games/preview-session", response_model=GuestGameLaunchResponse)
def launch_guest_game_preview_route(
    payload: GuestGameLaunchRequest,
    request: Request,
    guest_session_token: str | None = Header(default=None, alias="X-Guest-Session"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return generate_guest_classic_preview_session(
            db,
            guest_session_token,
            payload.story_id,
            payload.item_count,
            _client_ip(request),
        )
    except GuestServiceError as exc:
        return _error_response(exc)
