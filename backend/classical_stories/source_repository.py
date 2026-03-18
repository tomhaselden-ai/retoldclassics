from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

source_stories_table = Table(
    "stories",
    metadata,
    Column("story_id", Integer, primary_key=True),
    Column("source_author", String(100)),
    Column("source_story_id", Integer),
    Column("title", String(255)),
    Column("age_range", String(50)),
    Column("reading_level", String(50)),
    Column("moral", Text),
    Column("characters", JSON),
    Column("locations", JSON),
    Column("traits", JSON),
    Column("themes", JSON),
    Column("scenes", JSON),
    Column("beats", JSON),
    Column("paragraphs_modern", JSON),
    Column("narration", JSON),
    Column("illustration_prompts", JSON),
    Column("created_at", TIMESTAMP),
)


@dataclass
class SourceStoryRecord:
    story_id: int
    source_author: str | None
    source_story_id: int | None
    title: str | None
    age_range: str | None
    reading_level: str | None
    moral: str | None
    characters: Any
    locations: Any
    traits: Any
    themes: Any
    scenes: Any
    beats: Any
    paragraphs_modern: Any
    narration: Any
    illustration_prompts: Any
    created_at: datetime | None


def _to_source_story(row) -> SourceStoryRecord | None:
    if row is None:
        return None
    return SourceStoryRecord(
        story_id=row.story_id,
        source_author=row.source_author,
        source_story_id=row.source_story_id,
        title=row.title,
        age_range=row.age_range,
        reading_level=row.reading_level,
        moral=row.moral,
        characters=row.characters,
        locations=row.locations,
        traits=row.traits,
        themes=row.themes,
        scenes=row.scenes,
        beats=row.beats,
        paragraphs_modern=row.paragraphs_modern,
        narration=row.narration,
        illustration_prompts=row.illustration_prompts,
        created_at=row.created_at,
    )


def fetch_story_batch(db: Session, offset: int, limit: int) -> list[SourceStoryRecord]:
    rows = db.execute(
        select(source_stories_table)
        .order_by(source_stories_table.c.story_id.asc())
        .offset(offset)
        .limit(limit)
    ).mappings().all()
    return [_to_source_story(row) for row in rows]
