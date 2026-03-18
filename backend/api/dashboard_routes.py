from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.dashboard.dashboard_service import get_account_dashboard, get_reader_dashboard
from backend.db.database import get_db


router = APIRouter(tags=["dashboard"])


class ReadingStatisticsResponse(BaseModel):
    stories_read: int | None
    words_mastered: int | None
    reading_speed: float | None
    preferred_themes: Any
    traits_reinforced: Any


class RecentStoryResponse(BaseModel):
    story_id: int
    title: str | None
    created_at: datetime | None


class VocabularyProgressResponse(BaseModel):
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


class GameResultResponse(BaseModel):
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


class ReaderDashboardResponse(BaseModel):
    reader_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    trait_focus: Any
    reading_statistics: ReadingStatisticsResponse
    recent_stories: list[RecentStoryResponse]
    vocabulary_progress: list[VocabularyProgressResponse]
    game_results: list[GameResultResponse]


class AccountDashboardResponse(BaseModel):
    account_id: int
    readers: list[ReaderDashboardResponse]


@router.get("/accounts/{account_id}/dashboard", response_model=AccountDashboardResponse)
def get_account_dashboard_route(
    account_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if current_account.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account dashboard access denied",
        )
    return get_account_dashboard(db, account_id)


@router.get("/readers/{reader_id}/dashboard", response_model=ReaderDashboardResponse)
def get_reader_dashboard_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reader_dashboard(db, current_account.account_id, reader_id)
