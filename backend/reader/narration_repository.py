from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

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
class NarrationRecord:
    audio_id: int
    story_id: int | None
    scene_id: int | None
    audio_url: str | None
    speech_marks_json: Any
    voice: str | None
    generated_at: datetime | None


def _to_narration(row) -> NarrationRecord | None:
    if row is None:
        return None
    return NarrationRecord(
        audio_id=row.audio_id,
        story_id=row.story_id,
        scene_id=row.scene_id,
        audio_url=row.audio_url,
        speech_marks_json=row.speech_marks_json,
        voice=row.voice,
        generated_at=row.generated_at,
    )


def get_story_narration_map(db: Session, story_id: int) -> dict[int, NarrationRecord]:
    rows = db.execute(
        select(narration_audio_table)
        .where(narration_audio_table.c.story_id == story_id)
        .order_by(narration_audio_table.c.scene_id.asc())
    ).mappings().all()
    return {
        narration.scene_id: narration
        for narration in (_to_narration(row) for row in rows)
        if narration is not None and narration.scene_id is not None
    }


def get_scene_narration(db: Session, story_id: int, scene_id: int) -> NarrationRecord:
    row = db.execute(
        select(narration_audio_table).where(
            and_(
                narration_audio_table.c.story_id == story_id,
                narration_audio_table.c.scene_id == scene_id,
            )
        )
    ).mappings().first()
    narration = _to_narration(row)
    if narration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narration missing",
        )
    return narration
