from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.media_jobs.job_repository import (
    MediaJobRecord,
    create_completed_media_job,
    create_media_job,
    get_active_story_media_job,
    get_latest_story_media_job,
    get_media_job_for_account,
)
from backend.narration.narration_service import NarrationService
from backend.visuals.illustration_service import IllustrationService


JOB_TYPE_NARRATION = "narration"
JOB_TYPE_ILLUSTRATION = "illustration"
SUPPORTED_JOB_TYPES = {JOB_TYPE_NARRATION, JOB_TYPE_ILLUSTRATION}


class MediaJobService:
    def __init__(
        self,
        narration_service: NarrationService | None = None,
        illustration_service: IllustrationService | None = None,
    ) -> None:
        self._narration_service = narration_service or NarrationService()
        self._illustration_service = illustration_service or IllustrationService()

    def _validate_job_type(self, job_type: str) -> None:
        if job_type not in SUPPORTED_JOB_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media job type")

    def enqueue_story_job(self, db: Session, account_id: int, story_id: int, job_type: str) -> tuple[MediaJobRecord, bool]:
        self._validate_job_type(job_type)

        if job_type == JOB_TYPE_NARRATION and self._narration_service.story_has_complete_narration(db, account_id, story_id):
            latest = get_latest_story_media_job(db, account_id, story_id, job_type)
            if latest is not None:
                return latest, True
            job = create_completed_media_job(
                db,
                account_id,
                story_id,
                job_type,
                self._narration_service.get_story_narration_summary(db, account_id, story_id),
            )
            db.commit()
            return job, True

        if job_type == JOB_TYPE_ILLUSTRATION and self._illustration_service.story_has_illustration(db, account_id, story_id):
            latest = get_latest_story_media_job(db, account_id, story_id, job_type)
            if latest is not None:
                return latest, True
            job = create_completed_media_job(
                db,
                account_id,
                story_id,
                job_type,
                self._illustration_service.get_story_illustration_summary(db, account_id, story_id),
            )
            db.commit()
            return job, True

        active_job = get_active_story_media_job(db, account_id, story_id, job_type)
        if active_job is not None:
            return active_job, False

        job = create_media_job(db, account_id, story_id, job_type)
        db.commit()
        return job, False

    def get_job(self, db: Session, account_id: int, job_id: int) -> MediaJobRecord:
        return get_media_job_for_account(db, job_id, account_id)

    def get_latest_job(self, db: Session, account_id: int, story_id: int, job_type: str) -> MediaJobRecord | None:
        self._validate_job_type(job_type)
        return get_latest_story_media_job(db, account_id, story_id, job_type)
