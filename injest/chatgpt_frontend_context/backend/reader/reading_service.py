import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.reader.illustration_repository import (
    get_scene_illustration,
    get_scene_illustration_map,
)
from backend.reader.narration_repository import (
    get_scene_narration,
    get_story_narration_map,
)
from backend.reader.scene_repository import (
    extract_scene_text,
    get_story_for_account,
    get_story_scene,
    get_story_scenes,
)


def _build_scene_payload(scene, narration, illustration) -> dict[str, Any]:
    illustration_url = illustration.image_url if illustration is not None else None
    if not illustration_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Illustration missing",
        )

    audio_url = narration.audio_url if narration is not None else None
    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narration missing",
        )

    return {
        "scene_id": scene.scene_id,
        "scene_order": scene.scene_order,
        "scene_text": extract_scene_text(scene.scene_text),
        "illustration_url": illustration_url,
        "audio_url": audio_url,
        "speech_marks_json": narration.speech_marks_json,
    }


def get_reading_payload(db: Session, account_id: int, story_id: int) -> dict[str, Any]:
    logging.info("Loading immersive reading data for story %s", story_id)
    get_story_for_account(db, story_id, account_id)

    logging.info("Loading scenes")
    scenes = get_story_scenes(db, story_id)
    scene_ids = [scene.scene_id for scene in scenes]

    logging.info("Loading narration audio")
    narration_map = get_story_narration_map(db, story_id)

    logging.info("Loading illustrations")
    illustration_map = get_scene_illustration_map(db, scene_ids)

    payload_scenes = []
    for scene in scenes:
        narration = narration_map.get(scene.scene_id)
        illustration = illustration_map.get(scene.scene_id)
        payload_scenes.append(_build_scene_payload(scene, narration, illustration))

    logging.info("Reading payload generated")
    return {
        "story_id": story_id,
        "scenes": payload_scenes,
    }


def get_scene_reading_payload(
    db: Session,
    account_id: int,
    story_id: int,
    scene_id: int,
) -> dict[str, Any]:
    get_story_for_account(db, story_id, account_id)
    scene = get_story_scene(db, story_id, scene_id)
    narration = get_scene_narration(db, story_id, scene.scene_id)
    illustration = get_scene_illustration(db, scene.scene_id)
    return _build_scene_payload(scene, narration, illustration)
