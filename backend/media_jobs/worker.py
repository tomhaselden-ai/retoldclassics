from __future__ import annotations

import logging
import socket
import time
from uuid import uuid4

from fastapi import HTTPException

from backend.config.settings import MEDIA_WORKER_IDLE_SECONDS, MEDIA_WORKER_MAX_JOBS_PER_CYCLE
from backend.db.database import SessionLocal
from backend.media_jobs.job_repository import claim_next_media_job, complete_media_job, fail_media_job
from backend.media_jobs.job_service import JOB_TYPE_ILLUSTRATION, JOB_TYPE_NARRATION
from backend.narration.narration_service import NarrationService
from backend.visuals.illustration_service import IllustrationService


logger = logging.getLogger(__name__)


class MediaWorker:
    def __init__(
        self,
        worker_id: str | None = None,
        narration_service: NarrationService | None = None,
        illustration_service: IllustrationService | None = None,
    ) -> None:
        host = socket.gethostname() or "worker"
        self._worker_id = worker_id or f"{host}-{uuid4().hex[:8]}"
        self._narration_service = narration_service or NarrationService()
        self._illustration_service = illustration_service or IllustrationService()

    def _process_job(self, job) -> None:
        db = SessionLocal()
        try:
            if job.job_type == JOB_TYPE_NARRATION:
                result = self._narration_service.narrate_story(db, job.account_id, job.story_id)
            elif job.job_type == JOB_TYPE_ILLUSTRATION:
                result = self._illustration_service.generate_story_illustration(db, job.account_id, job.story_id)
            else:
                raise RuntimeError(f"Unsupported media job type: {job.job_type}")

            complete_media_job(db, job.job_id, result)
            logger.info("Completed media job", extra={"job_id": job.job_id, "job_type": job.job_type, "story_id": job.story_id})
        except HTTPException as exc:
            db.rollback()
            fail_media_job(db, job.job_id, str(exc.detail))
            logger.warning(
                "Media job failed with handled error",
                extra={"job_id": job.job_id, "job_type": job.job_type, "story_id": job.story_id, "detail": exc.detail},
            )
        except Exception as exc:
            db.rollback()
            fail_media_job(db, job.job_id, "Media job failed")
            logger.exception(
                "Media job failed",
                extra={"job_id": job.job_id, "job_type": job.job_type, "story_id": job.story_id},
            )
        finally:
            db.close()

    def run_cycle(self) -> int:
        processed = 0
        for _ in range(max(1, MEDIA_WORKER_MAX_JOBS_PER_CYCLE)):
            db = SessionLocal()
            try:
                job = claim_next_media_job(db, self._worker_id)
            finally:
                db.close()

            if job is None:
                break

            processed += 1
            self._process_job(job)
        return processed

    def run_forever(self) -> None:
        logger.info("Starting media worker", extra={"worker_id": self._worker_id})
        while True:
            processed = self.run_cycle()
            if processed == 0:
                time.sleep(max(1, MEDIA_WORKER_IDLE_SECONDS))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    MediaWorker().run_forever()


if __name__ == "__main__":
    main()
