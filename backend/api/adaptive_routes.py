from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.adaptive.adaptive_service import get_adaptive_profile, get_recommendations
from backend.auth.token_manager import get_current_account
from backend.db.database import get_db


router = APIRouter(tags=["adaptive"])


class RecommendedWordResponse(BaseModel):
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


class AdaptiveProfileResponse(BaseModel):
    reader_id: int
    reading_level: str | None
    stories_read: int | None
    words_mastered: int | None
    reading_speed: float | None
    proficiency: str
    recommended_story_difficulty: int
    recommended_vocabulary_difficulty: int
    recommended_game_difficulty: int


class AdaptiveRecommendationsResponse(BaseModel):
    recommended_words: list[RecommendedWordResponse]
    recommended_story_parameters: Any
    recommended_game_difficulty: int


@router.get("/readers/{reader_id}/adaptive-profile", response_model=AdaptiveProfileResponse)
def get_adaptive_profile_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_adaptive_profile(db, current_account.account_id, reader_id)


@router.get("/readers/{reader_id}/recommendations", response_model=AdaptiveRecommendationsResponse)
def get_recommendations_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_recommendations(db, current_account.account_id, reader_id)
