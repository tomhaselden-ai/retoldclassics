from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.story_engine.story_engine import generate_story_for_reader


router = APIRouter(prefix="/stories", tags=["stories"])


class StoryGenerateRequest(BaseModel):
    reader_id: int
    world_id: int
    theme: str = Field(min_length=1, max_length=100)
    target_length: str = Field(min_length=1, max_length=50)


class StoryGenerateResponse(BaseModel):
    story_id: int
    title: str
    summary: str


@router.post("/generate", response_model=StoryGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_story_route(
    payload: StoryGenerateRequest,
    current_account: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return generate_story_for_reader(
        db=db,
        account_id=current_account.account_id,
        reader_id=payload.reader_id,
        world_id=payload.world_id,
        theme=payload.theme,
        target_length=payload.target_length,
    )
