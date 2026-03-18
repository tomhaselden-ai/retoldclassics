from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.api.rate_limit import build_rate_limit_dependency
from backend.auth.token_manager import get_current_account
from backend.config.settings import RATE_LIMIT_MEDIA_REQUESTS, RATE_LIMIT_MEDIA_WINDOW_SECONDS
from backend.db.database import get_db
from backend.media_jobs.job_service import JOB_TYPE_NARRATION, MediaJobService


router = APIRouter(prefix="/stories", tags=["narration"])
narration_rate_limit = build_rate_limit_dependency(
    "story_narrate",
    RATE_LIMIT_MEDIA_REQUESTS,
    RATE_LIMIT_MEDIA_WINDOW_SECONDS,
    key_scope="account",
    account_dependency=get_current_account,
)


class NarrationJobResponse(BaseModel):
    job_id: int
    account_id: int
    story_id: int
    job_type: str
    status: str
    error_message: str | None
    result_payload: Any
    worker_id: str | None
    attempt_count: int
    created_at: datetime | None
    updated_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    already_ready: bool = False


class NarrationMetadataResponse(BaseModel):
    scene_id: int | None
    audio_url: str | None
    speech_marks_json: Any
    voice: str | None
    generated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


@router.post("/{story_id}/narrate", response_model=NarrationJobResponse, status_code=status.HTTP_202_ACCEPTED)
def narrate_story_route(
    story_id: int,
    request: Request,
    _: None = Depends(narration_rate_limit),
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = MediaJobService()
    job, already_ready = service.enqueue_story_job(db, current_account.account_id, story_id, JOB_TYPE_NARRATION)
    return NarrationJobResponse(**job.__dict__, already_ready=already_ready)


@router.get("/{story_id}/narration", response_model=list[NarrationMetadataResponse])
def get_story_narration_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    from backend.narration.narration_service import NarrationService

    service = NarrationService()
    return service.get_story_narration(db, current_account.account_id, story_id)
