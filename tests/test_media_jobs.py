import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.media_jobs.job_service import (
    JOB_TYPE_ILLUSTRATION,
    JOB_TYPE_NARRATION,
    MediaJobService,
)


class MediaJobServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Mock()
        self.narration_service = Mock()
        self.illustration_service = Mock()
        self.service = MediaJobService(
            narration_service=self.narration_service,
            illustration_service=self.illustration_service,
        )

    def test_enqueue_story_job_returns_existing_completed_job_when_narration_ready(self) -> None:
        ready_job = SimpleNamespace(job_id=11, status="completed")
        self.narration_service.story_has_complete_narration.return_value = True

        with patch("backend.media_jobs.job_service.get_latest_story_media_job", return_value=ready_job) as latest_job:
            job, already_ready = self.service.enqueue_story_job(self.db, 5, 9, JOB_TYPE_NARRATION)

        self.assertIs(job, ready_job)
        self.assertTrue(already_ready)
        latest_job.assert_called_once_with(self.db, 5, 9, JOB_TYPE_NARRATION)

    def test_enqueue_story_job_reuses_active_job(self) -> None:
        active_job = SimpleNamespace(job_id=12, status="processing")
        self.narration_service.story_has_complete_narration.return_value = False
        self.illustration_service.story_has_illustration.return_value = False

        with patch("backend.media_jobs.job_service.get_active_story_media_job", return_value=active_job) as active_lookup:
            job, already_ready = self.service.enqueue_story_job(self.db, 5, 9, JOB_TYPE_NARRATION)

        self.assertIs(job, active_job)
        self.assertFalse(already_ready)
        active_lookup.assert_called_once_with(self.db, 5, 9, JOB_TYPE_NARRATION)

    def test_enqueue_story_job_creates_job_when_no_media_exists(self) -> None:
        queued_job = SimpleNamespace(job_id=13, status="pending")
        self.narration_service.story_has_complete_narration.return_value = False
        self.illustration_service.story_has_illustration.return_value = False

        with patch("backend.media_jobs.job_service.get_active_story_media_job", return_value=None), patch(
            "backend.media_jobs.job_service.create_media_job",
            return_value=queued_job,
        ) as create_job:
            job, already_ready = self.service.enqueue_story_job(self.db, 7, 14, JOB_TYPE_ILLUSTRATION)

        self.assertIs(job, queued_job)
        self.assertFalse(already_ready)
        create_job.assert_called_once_with(self.db, 7, 14, JOB_TYPE_ILLUSTRATION)

    def test_enqueue_story_job_creates_completed_job_when_illustration_exists_without_prior_job(self) -> None:
        completed_job = SimpleNamespace(job_id=14, status="completed")
        self.narration_service.story_has_complete_narration.return_value = False
        self.illustration_service.story_has_illustration.return_value = True
        self.illustration_service.get_story_illustration_summary.return_value = {"story_id": 14, "image_url": "/image.png"}

        with patch("backend.media_jobs.job_service.get_latest_story_media_job", return_value=None), patch(
            "backend.media_jobs.job_service.create_completed_media_job",
            return_value=completed_job,
        ) as create_completed:
            job, already_ready = self.service.enqueue_story_job(self.db, 7, 14, JOB_TYPE_ILLUSTRATION)

        self.assertIs(job, completed_job)
        self.assertTrue(already_ready)
        create_completed.assert_called_once_with(
            self.db,
            7,
            14,
            JOB_TYPE_ILLUSTRATION,
            {"story_id": 14, "image_url": "/image.png"},
        )


if __name__ == "__main__":
    unittest.main()
