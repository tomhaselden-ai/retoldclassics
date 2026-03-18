from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.classics.classics_service import (
    ClassicsServiceError,
    get_classic_story_detail,
    get_classic_story_read_payload,
    get_classics_discovery,
    get_classics_shelf,
)
from backend.db.database import get_db


router = APIRouter(prefix="/classics", tags=["classics"])


class CoverResponse(BaseModel):
    mode: str
    image_url: str | None
    accent_token: str | None = None
    display_title: str | None = None


class ShelfItemResponse(BaseModel):
    story_id: int
    title: str | None
    source_author: str | None
    age_range: str | None
    reading_level: str | None
    preview_text: str
    cover: CoverResponse
    immersive_reader_available: bool
    narration_available: bool = False


class ShelfGroupResponse(BaseModel):
    author: str
    items: list[ShelfItemResponse]


class ClassicsDiscoveryResponse(BaseModel):
    items: list[ShelfItemResponse]
    total_count: int
    limit: int
    offset: int
    query: str | None
    applied_author: str | None
    match_mode: str
    prompt_examples: list[str]


class ClassicsShelfResponse(BaseModel):
    groups: list[ShelfGroupResponse]
    total_count: int
    limit: int
    offset: int


class ClassicStoryDetailResponse(BaseModel):
    story_id: int
    title: str | None
    source_author: str | None
    source_story_id: int | None
    age_range: str | None
    reading_level: str | None
    moral: str | None
    characters: Any
    locations: Any
    traits: Any
    themes: Any
    cover: CoverResponse
    summary: str
    immersive_reader_available: bool


class UnitIllustrationResponse(BaseModel):
    mode: str
    image_url: str | None
    prompt_excerpt: str | None


class SpeechMarkResponse(BaseModel):
    time: int | None
    type: str | None
    start: int | None
    end: int | None
    value: str | None


class ClassicReadUnitResponse(BaseModel):
    unit_id: str
    unit_order: int
    unit_type: str
    scene_title: str | None
    text: str
    narration_text: str | None
    audio_start_ms: int | None = None
    audio_end_ms: int | None = None
    speech_marks: list[SpeechMarkResponse] = []
    illustration: UnitIllustrationResponse


class ClassicReadResponse(BaseModel):
    story_id: int
    title: str | None
    source_author: str | None
    age_range: str | None
    reading_level: str | None
    cover: CoverResponse
    reader_mode: str
    has_scene_groups: bool
    has_paragraphs: bool
    has_narration_text: bool
    audio_url: str | None = None
    voice: str | None = None
    generated_at: str | None = None
    narration_available: bool = False
    units: list[ClassicReadUnitResponse]
    moral: str | None
    characters: Any
    locations: Any
    traits: Any
    themes: Any


def _error_response(exc: ClassicsServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/discover", response_model=ClassicsDiscoveryResponse)
def get_classics_discovery_route(
    author: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return get_classics_discovery(db, author=author, q=q, limit=limit, offset=offset)
    except ClassicsServiceError as exc:
        return _error_response(exc)


@router.get("/shelf", response_model=ClassicsShelfResponse)
def get_classics_shelf_route(
    author: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return get_classics_shelf(db, author=author, q=q, limit=limit, offset=offset)
    except ClassicsServiceError as exc:
        return _error_response(exc)


@router.get("/stories/{story_id}", response_model=ClassicStoryDetailResponse)
def get_classic_story_detail_route(
    story_id: int,
    db: Session = Depends(get_db),
) -> Any:
    try:
        return get_classic_story_detail(db, story_id)
    except ClassicsServiceError as exc:
        return _error_response(exc)


@router.get("/stories/{story_id}/read", response_model=ClassicReadResponse)
def get_classic_story_read_route(
    story_id: int,
    db: Session = Depends(get_db),
) -> Any:
    try:
        return get_classic_story_read_payload(db, story_id)
    except ClassicsServiceError as exc:
        return _error_response(exc)
