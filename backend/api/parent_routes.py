from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.analytics.analytics_service import AnalyticsServiceError
from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.goals.goal_service import GoalServiceError
from backend.parent.analytics_service import ParentAnalyticsServiceError, get_parent_analytics
from backend.parent.summary_service import get_parent_reader_summary, get_parent_summary


router = APIRouter(prefix="/parent", tags=["parent"])


class ParentAggregateStatisticsResponse(BaseModel):
    stories_read: int
    words_mastered: int
    tracked_words: int
    games_played: int
    average_game_score: float | None


class ParentSummaryReaderResponse(BaseModel):
    reader_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    trait_focus: list[str]
    proficiency: str
    stories_read: int
    words_mastered: int
    average_game_score: float | None
    strengths: list[str]
    focus_message: str | None
    recommended_story_difficulty: int | None
    recommended_vocabulary_difficulty: int | None
    recommended_game_difficulty: int | None


class ParentSummaryResponse(BaseModel):
    account_id: int
    reader_count: int
    aggregate_statistics: ParentAggregateStatisticsResponse
    readers: list[ParentSummaryReaderResponse]


class ParentAnalyticsFocusAreaResponse(BaseModel):
    category: str
    priority: int
    message: str


class ParentAnalyticsRecommendationResponse(BaseModel):
    recommended_story_difficulty: int
    recommended_vocabulary_difficulty: int
    recommended_game_difficulty: int


class ParentAnalyticsGoalProgressResponse(BaseModel):
    current_value: int
    target_value: int
    progress_percent: int
    status: str
    updated_at: datetime | None
    completed_at: datetime | None


class ParentAnalyticsGoalResponse(BaseModel):
    goal_id: int
    reader_id: int
    goal_type: str
    title: str
    target_value: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    progress: ParentAnalyticsGoalProgressResponse


class ParentAnalyticsGoalSummaryResponse(BaseModel):
    active_goal_count: int
    completed_goal_count: int


class ParentAnalyticsAccuracyByTypeResponse(BaseModel):
    game_type: str
    sessions_played: int
    words_attempted: int
    words_correct: int
    success_rate: float | None


class ParentAnalyticsRepeatedMissedWordResponse(BaseModel):
    word_text: str
    miss_count: int


class ParentAnalyticsGamePracticeResponse(BaseModel):
    sessions_total: int
    sessions_this_week: int
    words_practiced: int
    words_correct: int
    average_success_rate: float | None
    practice_time_seconds: int
    strongest_game_type: str | None
    weakest_game_type: str | None
    improvement_trend: str
    accuracy_by_game_type: list[ParentAnalyticsAccuracyByTypeResponse]
    repeated_missed_words: list[ParentAnalyticsRepeatedMissedWordResponse]


class ParentAnalyticsReaderResponse(BaseModel):
    reader_id: int
    name: str | None
    reading_level: str | None
    proficiency: str
    stories_read: int
    words_mastered: int
    average_game_score: float | None
    strengths: list[str]
    focus_areas: list[ParentAnalyticsFocusAreaResponse]
    recommendations: ParentAnalyticsRecommendationResponse
    game_practice: ParentAnalyticsGamePracticeResponse
    goals: list[ParentAnalyticsGoalResponse]


class ParentAnalyticsResponse(BaseModel):
    account_id: int
    reader_count: int
    aggregate_statistics: ParentAggregateStatisticsResponse
    aggregate_game_practice: ParentAnalyticsGamePracticeResponse
    goal_summary: ParentAnalyticsGoalSummaryResponse
    readers: list[ParentAnalyticsReaderResponse]


class ParentReaderResponse(BaseModel):
    reader_id: int
    account_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    gender_preference: str | None
    trait_focus: list[str]
    created_at: datetime | None


class ParentReaderRecentStoryResponse(BaseModel):
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


class ParentReaderWorldResponse(BaseModel):
    reader_world_id: int
    world_id: int | None
    custom_name: str | None
    name: str | None
    description: str | None


class ParentReaderSummaryResponse(BaseModel):
    reader: ParentReaderResponse
    dashboard: dict[str, Any]
    learning_insights: dict[str, Any]
    library_summary: dict[str, Any]
    world_summary: dict[str, Any]


def _error_response(exc: AnalyticsServiceError | GoalServiceError | ParentAnalyticsServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/summary", response_model=ParentSummaryResponse)
def get_parent_summary_route(
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_parent_summary(db, current_account.account_id)


@router.get("/analytics", response_model=ParentAnalyticsResponse)
def get_parent_analytics_route(
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_parent_analytics(db, current_account.account_id)
    except (AnalyticsServiceError, GoalServiceError, ParentAnalyticsServiceError) as exc:
        return _error_response(exc)


@router.get("/readers/{reader_id}/summary", response_model=ParentReaderSummaryResponse)
def get_parent_reader_summary_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_parent_reader_summary(db, current_account.account_id, reader_id)
