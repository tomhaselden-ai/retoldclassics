from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.library.library_service import (
    LibraryServiceError,
    get_library_story_detail,
    get_reader_library,
    publish_library_story,
)


router = APIRouter(prefix="/readers", tags=["library"])


class LibraryStoryResponse(BaseModel):
    story_id: int
    title: str | None
    trait_focus: str | None
    current_version: int | None
    created_at: datetime | None
    updated_at: datetime | None
    reader_world_id: int | None
    world_id: int | None
    world_name: str | None
    custom_world_name: str | None
    published: bool
    epub_url: str | None
    epub_created_at: datetime | None


class ReaderLibraryResponse(BaseModel):
    reader_id: int
    reader_name: str | None
    bookshelf_id: int
    bookshelf_created_at: datetime | None
    story_count: int
    stories: list[LibraryStoryResponse]


class LibraryStoryDetailResponse(BaseModel):
    reader_id: int
    reader_name: str | None
    bookshelf_id: int
    story: LibraryStoryResponse


class PublishLibraryStoryResponse(BaseModel):
    status: str
    story_id: int
    epub_url: str
    story: LibraryStoryResponse


def _error_response(exc: LibraryServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/{reader_id}/library", response_model=ReaderLibraryResponse)
def get_reader_library_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_reader_library(db, current_account.account_id, reader_id)
    except LibraryServiceError as exc:
        return _error_response(exc)


@router.get("/{reader_id}/library/{story_id}", response_model=LibraryStoryDetailResponse)
def get_library_story_detail_route(
    reader_id: int,
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_library_story_detail(db, current_account.account_id, reader_id, story_id)
    except LibraryServiceError as exc:
        return _error_response(exc)


@router.post(
    "/{reader_id}/library/{story_id}/publish",
    response_model=PublishLibraryStoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def publish_library_story_route(
    reader_id: int,
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return publish_library_story(db, current_account.account_id, reader_id, story_id)
    except LibraryServiceError as exc:
        return _error_response(exc)
