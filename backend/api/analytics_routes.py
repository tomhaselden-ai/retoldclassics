from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.analytics.analytics_service import (
    AnalyticsServiceError,
    get_account_learning_insights,
    get_reader_learning_insights,
)
from backend.auth.token_manager import get_current_account
from backend.db.database import get_db


router = APIRouter(tags=["analytics"])


class RecentWordResponse(BaseModel):
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


class FocusAreaResponse(BaseModel):
    category: str
    priority: int
    message: str


class ReadingSummaryResponse(BaseModel):
    stories_read: int
    words_mastered: int
    reading_speed: float | None
    preferred_themes: Any
    traits_reinforced: Any


class StorySummaryResponse(BaseModel):
    recent_story_count: int
    latest_story_title: str | None
    latest_story_at: datetime | None


class VocabularySummaryResponse(BaseModel):
    tracked_words: int
    mastered_words: int
    developing_words: int
    needs_practice_words: int
    recent_words: list[RecentWordResponse]


class GameSummaryResponse(BaseModel):
    total_games_played: int
    average_score: float | None
    average_duration_seconds: float | None
    strongest_game_type: str | None
    most_recent_game_type: str | None
    most_recent_game_at: datetime | None


class RecommendationSummaryResponse(BaseModel):
    recommended_story_difficulty: int
    recommended_vocabulary_difficulty: int
    recommended_game_difficulty: int


class ReaderLearningInsightsResponse(BaseModel):
    reader_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    trait_focus: Any
    proficiency: str
    reading_summary: ReadingSummaryResponse
    story_summary: StorySummaryResponse
    vocabulary_summary: VocabularySummaryResponse
    game_summary: GameSummaryResponse
    recommendations: RecommendationSummaryResponse
    strengths: list[str]
    focus_areas: list[FocusAreaResponse]


class AggregateStatisticsResponse(BaseModel):
    stories_read: int
    words_mastered: int
    tracked_words: int
    games_played: int
    average_game_score: float | None


class AccountReaderInsightsResponse(BaseModel):
    reader_id: int
    name: str | None
    reading_level: str | None
    proficiency: str
    stories_read: int
    words_mastered: int
    average_game_score: float | None
    strengths: list[str]
    focus_areas: list[FocusAreaResponse]
    recommendations: RecommendationSummaryResponse


class AccountLearningInsightsResponse(BaseModel):
    account_id: int
    reader_count: int
    aggregate_statistics: AggregateStatisticsResponse
    readers: list[AccountReaderInsightsResponse]


def _error_response(exc: AnalyticsServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get(
    "/readers/{reader_id}/learning-insights",
    response_model=ReaderLearningInsightsResponse,
)
def get_reader_learning_insights_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_reader_learning_insights(db, current_account.account_id, reader_id)
    except AnalyticsServiceError as exc:
        return _error_response(exc)


@router.get(
    "/accounts/{account_id}/learning-insights",
    response_model=AccountLearningInsightsResponse,
)
def get_account_learning_insights_route(
    account_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_account_learning_insights(db, current_account.account_id, account_id)
    except AnalyticsServiceError as exc:
        return _error_response(exc)
