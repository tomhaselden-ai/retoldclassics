from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.visuals.illustration_service import IllustrationService


router = APIRouter(prefix="/stories", tags=["illustrations"])


class IllustrationResponse(BaseModel):
    story_id: int
    image_url: str
    scenes_illustrated: int


class IllustrationMetadataResponse(BaseModel):
    image_url: str


class SceneIllustrationMetadataResponse(BaseModel):
    scene_id: int
    scene_order: int | None
    image_url: str | None
    prompt_used: str | None
    generation_model: str | None
    generated_at: datetime | None


@router.post("/{story_id}/illustrate", response_model=IllustrationResponse, status_code=status.HTTP_201_CREATED)
def illustrate_story_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = IllustrationService()
    return service.generate_story_illustration(db, current_account.account_id, story_id)


@router.get("/{story_id}/illustration", response_model=IllustrationMetadataResponse)
def get_story_illustration_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = IllustrationService()
    return service.get_story_illustration(db, current_account.account_id, story_id)


@router.get("/{story_id}/illustrations", response_model=list[SceneIllustrationMetadataResponse])
def get_story_illustrations_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = IllustrationService()
    return service.get_story_illustrations(db, current_account.account_id, story_id)
