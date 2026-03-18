from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.reader.reading_service import get_reading_payload, get_scene_reading_payload


router = APIRouter(prefix="/stories", tags=["reading"])


class ReadingSceneResponse(BaseModel):
    scene_id: int
    scene_order: int | None
    scene_text: str
    illustration_url: str
    audio_url: str
    speech_marks_json: Any


class StoryReadingResponse(BaseModel):
    story_id: int
    scenes: list[ReadingSceneResponse]


@router.get("/{story_id}/read", response_model=StoryReadingResponse)
def get_story_reading_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reading_payload(db, current_account.account_id, story_id)


@router.get("/{story_id}/scene/{scene_id}", response_model=ReadingSceneResponse)
def get_story_scene_route(
    story_id: int,
    scene_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_scene_reading_payload(db, current_account.account_id, story_id, scene_id)
