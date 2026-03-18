from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.media_jobs.job_service import MediaJobService


router = APIRouter(tags=["media-jobs"])


class MediaJobResponse(BaseModel):
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


@router.get("/media-jobs/{job_id}", response_model=MediaJobResponse)
def get_media_job_route(
    job_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = MediaJobService()
    return service.get_job(db, current_account.account_id, job_id)


@router.get("/stories/{story_id}/media-jobs/{job_type}/latest", response_model=MediaJobResponse | None)
def get_latest_story_media_job_route(
    story_id: int,
    job_type: str,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = MediaJobService()
    return service.get_latest_job(db, current_account.account_id, story_id, job_type)
