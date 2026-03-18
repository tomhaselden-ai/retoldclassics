from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.reader_home.home_service import get_reader_home_summary


router = APIRouter(tags=["reader-home"])


class ReaderHomeReaderResponse(BaseModel):
    reader_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    trait_focus: Any


class ReaderHomeStoryResponse(BaseModel):
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


class ReaderHomeWordResponse(BaseModel):
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


class ReaderHomeGameResponse(BaseModel):
    game_result_id: int
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


class ReaderHomeLibrarySummaryResponse(BaseModel):
    story_count: int
    world_count: int


class ReaderHomeVocabularySummaryResponse(BaseModel):
    tracked_words: int
    practice_words: int
    mastered_words: int
    recommended_word: ReaderHomeWordResponse | None


class ReaderHomeGameSummaryResponse(BaseModel):
    recent_game: ReaderHomeGameResponse | None
    recommended_game_difficulty: int
    games_played_recently: int


class ReaderHomePathResponse(BaseModel):
    proficiency: str
    recommended_story_difficulty: int
    goal_message: str


class ReaderHomeSummaryResponse(BaseModel):
    reader: ReaderHomeReaderResponse
    continue_reading: ReaderHomeStoryResponse | None
    library_summary: ReaderHomeLibrarySummaryResponse
    vocabulary_summary: ReaderHomeVocabularySummaryResponse
    game_summary: ReaderHomeGameSummaryResponse
    reader_path: ReaderHomePathResponse


@router.get("/readers/{reader_id}/home", response_model=ReaderHomeSummaryResponse)
def get_reader_home_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_reader_home_summary(db, current_account.account_id, reader_id)
