from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.vocabulary.vocabulary_service import (
    get_reader_practice_vocabulary,
    get_reader_vocabulary,
    update_vocabulary_progress,
)


router = APIRouter(prefix="/readers", tags=["vocabulary"])


class ReaderVocabularyResponse(BaseModel):
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


class UpdateVocabularyProgressRequest(BaseModel):
    mastery_level: int = Field(ge=0, le=3)


class UpdateVocabularyProgressResponse(BaseModel):
    word_id: int
    mastery_level: int | None
    last_seen: datetime | None


@router.get("/{reader_id}/vocabulary", response_model=list[ReaderVocabularyResponse])
def get_reader_vocabulary_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reader_vocabulary(db, current_account.account_id, reader_id)


@router.post(
    "/{reader_id}/vocabulary/{word_id}/progress",
    response_model=UpdateVocabularyProgressResponse,
)
def update_vocabulary_progress_route(
    reader_id: int,
    word_id: int,
    payload: UpdateVocabularyProgressRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return update_vocabulary_progress(
        db,
        current_account.account_id,
        reader_id,
        word_id,
        payload.mastery_level,
    )


@router.get("/{reader_id}/vocabulary/practice", response_model=list[ReaderVocabularyResponse])
def get_reader_vocabulary_practice_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reader_practice_vocabulary(db, current_account.account_id, reader_id)
