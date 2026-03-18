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
from backend.narration.speechmark_alignment import normalize_speech_marks_for_text
from backend.narration.audio_storage import AudioStorageService
from backend.visuals.image_storage import IllustrationImageStorage


def _normalize_audio_url(audio_url: str | None) -> str | None:
    if not audio_url:
        return None
    return AudioStorageService().create_playback_url(audio_url)


def _normalize_illustration_url(image_url: str | None) -> str | None:
    if not image_url:
        return None
    return IllustrationImageStorage().normalize_public_url(image_url)


def _build_scene_payload(scene, narration, illustration) -> dict[str, Any]:
    scene_text = extract_scene_text(scene.scene_text)
    raw_illustration_url = illustration.image_url if illustration is not None else None
    illustration_url = _normalize_illustration_url(raw_illustration_url)
    raw_audio_url = narration.audio_url if narration is not None else None
    audio_url = _normalize_audio_url(raw_audio_url)
    speech_marks_json = normalize_speech_marks_for_text(
        scene_text,
        narration.speech_marks_json if narration is not None else [],
    )

    return {
        "scene_id": scene.scene_id,
        "scene_order": scene.scene_order,
        "scene_text": scene_text,
        "illustration_url": illustration_url,
        "audio_url": audio_url,
        "speech_marks_json": speech_marks_json,
    }


def get_reading_payload(db: Session, account_id: int, story_id: int) -> dict[str, Any]:
    logging.info("Loading immersive reading data for story %s", story_id)
    story = get_story_for_account(db, story_id, account_id)

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
        "title": story.title,
        "trait_focus": story.trait_focus,
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
