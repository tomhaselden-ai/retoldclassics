from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.orm import Session


metadata = MetaData()

illustrations_table = Table(
    "illustrations",
    metadata,
    Column("illustration_id", Integer, primary_key=True),
    Column("scene_id", Integer),
    Column("image_url", Text),
    Column("prompt_used", Text),
    Column("generation_model", String(100)),
    Column("generated_at", TIMESTAMP),
)


@dataclass
class IllustrationRecord:
    illustration_id: int
    scene_id: int | None
    image_url: str | None
    prompt_used: str | None
    generation_model: str | None
    generated_at: datetime | None


def _to_illustration(row) -> IllustrationRecord | None:
    if row is None:
        return None
    return IllustrationRecord(
        illustration_id=row.illustration_id,
        scene_id=row.scene_id,
        image_url=row.image_url,
        prompt_used=row.prompt_used,
        generation_model=row.generation_model,
        generated_at=row.generated_at,
    )


def get_scene_illustration_map(db: Session, scene_ids: list[int]) -> dict[int, IllustrationRecord]:
    if not scene_ids:
        return {}

    rows = db.execute(
        select(illustrations_table)
        .where(illustrations_table.c.scene_id.in_(scene_ids))
        .order_by(illustrations_table.c.scene_id.asc(), illustrations_table.c.illustration_id.asc())
    ).mappings().all()

    illustration_map: dict[int, IllustrationRecord] = {}
    for row in rows:
        illustration = _to_illustration(row)
        if illustration is None or illustration.scene_id is None:
            continue
        illustration_map.setdefault(illustration.scene_id, illustration)
    return illustration_map


def get_scene_illustration(db: Session, scene_id: int) -> IllustrationRecord:
    row = db.execute(
        select(illustrations_table)
        .where(illustrations_table.c.scene_id == scene_id)
        .order_by(illustrations_table.c.illustration_id.asc())
    ).mappings().first()
    illustration = _to_illustration(row)
    if illustration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Illustration missing",
        )
    return illustration
