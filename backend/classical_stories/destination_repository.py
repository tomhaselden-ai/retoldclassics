from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, or_, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session

from backend.classical_stories.source_repository import SourceStoryRecord


metadata = MetaData()

destination_stories_table = Table(
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
class DestinationStoryRecord:
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


def _to_destination_story(row) -> DestinationStoryRecord | None:
    if row is None:
        return None
    return DestinationStoryRecord(
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


def get_existing_story_keys(
    db: Session,
    keys: list[tuple[str | None, int | None]],
) -> dict[tuple[str | None, int | None], int]:
    valid_keys = [(author, story_id) for author, story_id in keys if author is not None and story_id is not None]
    if not valid_keys:
        return {}

    conditions = [
        and_(
            destination_stories_table.c.source_author == author,
            destination_stories_table.c.source_story_id == story_id,
        )
        for author, story_id in valid_keys
    ]

    rows = db.execute(
        select(
            destination_stories_table.c.story_id,
            destination_stories_table.c.source_author,
            destination_stories_table.c.source_story_id,
        ).where(or_(*conditions))
    ).all()

    return {
        (row.source_author, row.source_story_id): row.story_id
        for row in rows
    }


def insert_story(db: Session, story: SourceStoryRecord) -> int:
    result = db.execute(
        destination_stories_table.insert().values(
            source_author=story.source_author,
            source_story_id=story.source_story_id,
            title=story.title,
            age_range=story.age_range,
            reading_level=story.reading_level,
            moral=story.moral,
            characters=story.characters,
            locations=story.locations,
            traits=story.traits,
            themes=story.themes,
            scenes=story.scenes,
            beats=story.beats,
            paragraphs_modern=story.paragraphs_modern,
            narration=story.narration,
            illustration_prompts=story.illustration_prompts,
            created_at=story.created_at,
        )
    )
    return int(result.inserted_primary_key[0])


def get_story_by_key(
    db: Session,
    source_author: str | None,
    source_story_id: int | None,
) -> DestinationStoryRecord | None:
    if source_author is None or source_story_id is None:
        return None

    row = db.execute(
        select(destination_stories_table).where(
            and_(
                destination_stories_table.c.source_author == source_author,
                destination_stories_table.c.source_story_id == source_story_id,
            )
        )
    ).mappings().first()
    return _to_destination_story(row)
