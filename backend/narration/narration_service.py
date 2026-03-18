import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config.settings import POLLY_DEFAULT_STYLE_MODE
from backend.narration.audio_storage import AudioStorageService
from backend.narration.narration_repository import (
    extract_scene_narration_text,
    get_narration_metadata,
    get_story_for_account,
    get_story_scenes,
    upsert_narration_audio,
)
from backend.narration.polly_client import PollyNarrationClient
from backend.narration.speechmark_alignment import normalize_speech_marks_for_text
from backend.narration.speechmark_parser import parse_speech_marks


MAX_WORKERS = 4


@dataclass
class SceneNarrationResult:
    scene_id: int
    audio_url: str
    speech_marks_json: list[dict]
    voice: str


class NarrationService:
    def __init__(
        self,
        polly_client: PollyNarrationClient | None = None,
        audio_storage: AudioStorageService | None = None,
    ) -> None:
        self._polly_client = polly_client
        self._audio_storage = audio_storage or AudioStorageService()

    def _generate_scene_narration(self, story_id: int, scene) -> SceneNarrationResult:
        scene_text = extract_scene_narration_text(scene)
        polly_client = self._polly_client or PollyNarrationClient()
        synthesis = polly_client.synthesize_storytelling_narration(
            scene_text,
            style_mode=POLLY_DEFAULT_STYLE_MODE,
            requires_speech_marks=True,
        )
        speech_marks_json = normalize_speech_marks_for_text(
            scene_text,
            parse_speech_marks(synthesis.speech_marks_raw),
        )
        audio_url = self._audio_storage.upload_scene_audio(story_id, scene.scene_id, synthesis.audio_bytes)

        logging.info("Scene %s narration generated", scene.scene_order or scene.scene_id)
        return SceneNarrationResult(
            scene_id=scene.scene_id,
            audio_url=audio_url,
            speech_marks_json=speech_marks_json,
            voice=synthesis.voice_plan.voice_id,
        )

    def _has_existing_narration(self, narration_record) -> bool:
        return bool(
            narration_record
            and narration_record.audio_url
            and narration_record.speech_marks_json
        )

    def story_has_complete_narration(self, db: Session, account_id: int, story_id: int) -> bool:
        story = get_story_for_account(db, story_id, account_id)
        scenes = get_story_scenes(db, story.story_id)
        existing_narration = {
            record.scene_id: record
            for record in get_narration_metadata(db, story.story_id)
            if record is not None and record.scene_id is not None
        }
        return all(self._has_existing_narration(existing_narration.get(scene.scene_id)) for scene in scenes)

    def get_story_narration_summary(self, db: Session, account_id: int, story_id: int) -> dict[str, int]:
        story = get_story_for_account(db, story_id, account_id)
        metadata = get_narration_metadata(db, story.story_id)
        completed = [record for record in metadata if self._has_existing_narration(record)]
        return {
            "story_id": story.story_id,
            "scenes_narrated": len(completed),
            "audio_files_created": len(completed),
        }

    def narrate_story(self, db: Session, account_id: int, story_id: int) -> dict[str, int]:
        story = get_story_for_account(db, story_id, account_id)
        scenes = get_story_scenes(db, story.story_id)
        existing_narration = {
            record.scene_id: record
            for record in get_narration_metadata(db, story.story_id)
            if record is not None and record.scene_id is not None
        }
        pending_scenes = [
            scene
            for scene in scenes
            if not self._has_existing_narration(existing_narration.get(scene.scene_id))
        ]

        logging.info("Generating narration for story %s", story.story_id)

        if not pending_scenes:
            logging.info("Narration already exists for story %s", story.story_id)
            return {
                "story_id": story.story_id,
                "scenes_narrated": 0,
                "audio_files_created": 0,
            }

        results: list[SceneNarrationResult] = []
        try:
            with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(pending_scenes))) as executor:
                futures = [
                    executor.submit(self._generate_scene_narration, story.story_id, scene)
                    for scene in pending_scenes
                ]

                for future in as_completed(futures):
                    results.append(future.result())

            for result in results:
                upsert_narration_audio(
                    db=db,
                    story_id=story.story_id,
                    scene_id=result.scene_id,
                    audio_url=result.audio_url,
                    speech_marks_json=result.speech_marks_json,
                    voice=result.voice,
                )

            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Narration generation failed",
            ) from exc

        logging.info("Upload complete")
        return {
            "story_id": story.story_id,
            "scenes_narrated": len(results),
            "audio_files_created": len(results),
        }

    def get_story_narration(self, db: Session, account_id: int, story_id: int) -> list:
        get_story_for_account(db, story_id, account_id)
        return get_narration_metadata(db, story_id)
