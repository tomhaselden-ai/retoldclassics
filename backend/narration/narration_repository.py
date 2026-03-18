import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

stories_generated_table = Table(
    "stories_generated",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("reader_world_id", Integer),
    Column("title", String(255)),
    Column("trait_focus", String(100)),
    Column("current_version", Integer),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

readers_table = Table(
    "readers",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("name", String(100)),
    Column("age", Integer),
    Column("reading_level", String(50)),
    Column("gender_preference", String(50)),
    Column("trait_focus", JSON),
    Column("created_at", TIMESTAMP),
)

story_scenes_table = Table(
    "story_scenes",
    metadata,
    Column("scene_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("scene_order", Integer),
    Column("scene_text", Text),
    Column("illustration_url", Text),
    Column("audio_url", Text),
)

narration_audio_table = Table(
    "narration_audio",
    metadata,
    Column("audio_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("scene_id", Integer),
    Column("audio_url", Text),
    Column("speech_marks_json", JSON),
    Column("voice", String(50)),
    Column("generated_at", TIMESTAMP),
)


@dataclass
class StoryRecord:
    story_id: int
    reader_id: int | None
    reader_world_id: int | None
    title: str | None
    trait_focus: str | None
    current_version: int | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class SceneRecord:
    scene_id: int
    story_id: int | None
    scene_order: int | None
    scene_text: str | None
    illustration_url: str | None
    audio_url: str | None


@dataclass
class NarrationAudioRecord:
    audio_id: int
    story_id: int | None
    scene_id: int | None
    audio_url: str | None
    speech_marks_json: Any
    voice: str | None
    generated_at: datetime | None


def _to_story(row) -> StoryRecord | None:
    if row is None:
        return None
    return StoryRecord(
        story_id=row.story_id,
        reader_id=row.reader_id,
        reader_world_id=row.reader_world_id,
        title=row.title,
        trait_focus=row.trait_focus,
        current_version=row.current_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_scene(row) -> SceneRecord | None:
    if row is None:
        return None
    return SceneRecord(
        scene_id=row.scene_id,
        story_id=row.story_id,
        scene_order=row.scene_order,
        scene_text=row.scene_text,
        illustration_url=row.illustration_url,
        audio_url=row.audio_url,
    )


def _to_narration_audio(row) -> NarrationAudioRecord | None:
    if row is None:
        return None
    return NarrationAudioRecord(
        audio_id=row.audio_id,
        story_id=row.story_id,
        scene_id=row.scene_id,
        audio_url=row.audio_url,
        speech_marks_json=row.speech_marks_json,
        voice=row.voice,
        generated_at=row.generated_at,
    )


def get_story_for_account(db: Session, story_id: int, account_id: int) -> StoryRecord:
    row = db.execute(
        select(stories_generated_table)
        .select_from(
            stories_generated_table.join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(
            and_(
                stories_generated_table.c.story_id == story_id,
                readers_table.c.account_id == account_id,
            )
        )
    ).mappings().first()

    story = _to_story(row)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found",
        )
    return story


def get_story_scenes(db: Session, story_id: int) -> list[SceneRecord]:
    rows = db.execute(
        select(story_scenes_table)
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
    ).mappings().all()

    scenes = [_to_scene(row) for row in rows]
    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story has no scenes",
        )
    return scenes


def upsert_narration_audio(
    db: Session,
    story_id: int,
    scene_id: int,
    audio_url: str,
    speech_marks_json: list[dict],
    voice: str,
) -> None:
    existing = db.execute(
        select(narration_audio_table.c.audio_id).where(
            and_(
                narration_audio_table.c.story_id == story_id,
                narration_audio_table.c.scene_id == scene_id,
            )
        )
    ).first()

    if existing is None:
        db.execute(
            narration_audio_table.insert().values(
                story_id=story_id,
                scene_id=scene_id,
                audio_url=audio_url,
                speech_marks_json=speech_marks_json,
                voice=voice,
            )
        )
        return

    db.execute(
        narration_audio_table.update()
        .where(narration_audio_table.c.audio_id == existing.audio_id)
        .values(
            audio_url=audio_url,
            speech_marks_json=speech_marks_json,
            voice=voice,
        )
    )


def get_narration_metadata(db: Session, story_id: int) -> list[NarrationAudioRecord]:
    rows = db.execute(
        select(narration_audio_table)
        .where(narration_audio_table.c.story_id == story_id)
        .order_by(narration_audio_table.c.scene_id.asc())
    ).mappings().all()
    return [_to_narration_audio(row) for row in rows]


def extract_scene_narration_text(scene: SceneRecord) -> str:
    if scene.scene_text is None or not scene.scene_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scene {scene.scene_id} has no narration text",
        )

    try:
        payload = json.loads(scene.scene_text)
    except json.JSONDecodeError:
        return scene.scene_text.strip()

    paragraphs = payload.get("paragraphs")
    if isinstance(paragraphs, list):
        text_parts = [paragraph.strip() for paragraph in paragraphs if isinstance(paragraph, str) and paragraph.strip()]
        if text_parts:
            return "\n\n".join(text_parts)
    if isinstance(paragraphs, str) and paragraphs.strip():
        return paragraphs.strip()

    scene_text = payload.get("scene_text")
    if isinstance(scene_text, str) and scene_text.strip():
        return scene_text.strip()

    return scene.scene_text.strip()
