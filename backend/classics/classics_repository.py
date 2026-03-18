from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, func, or_, select, update
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

stories_table = Table(
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
class ClassicalStoryRecord:
    story_id: int
    source_author: str | None
    source_story_id: int | None
    title: str | None
    age_range: str | None
    reading_level: str | None
    moral: str | None
    characters: object
    locations: object
    traits: object
    themes: object
    scenes: object
    beats: object
    paragraphs_modern: object
    narration: object
    illustration_prompts: object
    created_at: datetime | None


def _to_classical_story(row) -> ClassicalStoryRecord | None:
    if row is None:
        return None
    return ClassicalStoryRecord(
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


def _build_filter_query(authors: list[str], q: str | None):
    query = select(stories_table).where(stories_table.c.source_author.in_(authors))
    if q:
        lowered = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(stories_table.c.title).like(lowered),
                func.lower(stories_table.c.source_author).like(lowered),
            )
        )
    return query


def list_classical_stories(
    db: Session,
    authors: list[str],
    q: str | None,
    limit: int,
    offset: int,
) -> list[ClassicalStoryRecord]:
    rows = db.execute(
        _build_filter_query(authors, q)
        .order_by(stories_table.c.source_author.asc(), stories_table.c.title.asc(), stories_table.c.story_id.asc())
        .limit(limit)
        .offset(offset)
    ).mappings().all()
    return [_to_classical_story(row) for row in rows if _to_classical_story(row) is not None]


def count_classical_stories(
    db: Session,
    authors: list[str],
    q: str | None,
) -> int:
    subquery = _build_filter_query(authors, q).subquery()
    value = db.execute(select(func.count()).select_from(subquery)).scalar_one()
    return int(value or 0)


def get_classical_story(
    db: Session,
    story_id: int,
    authors: list[str],
) -> ClassicalStoryRecord | None:
    row = db.execute(
        select(stories_table).where(
            stories_table.c.story_id == story_id,
            stories_table.c.source_author.in_(authors),
        )
    ).mappings().first()
    return _to_classical_story(row)


def get_classical_stories_by_ids(
    db: Session,
    story_ids: list[int],
    authors: list[str],
) -> list[ClassicalStoryRecord]:
    if not story_ids:
        return []

    rows = db.execute(
        select(stories_table).where(
            stories_table.c.story_id.in_(story_ids),
            stories_table.c.source_author.in_(authors),
        )
    ).mappings().all()
    by_id = {
        story.story_id: story
        for story in (_to_classical_story(row) for row in rows)
        if story is not None
    }
    return [by_id[story_id] for story_id in story_ids if story_id in by_id]


def list_classical_story_candidates(
    db: Session,
    authors: list[str],
    story_id: int | None = None,
    limit: int | None = None,
    sort_order: str = "author",
) -> list[ClassicalStoryRecord]:
    query = select(stories_table).where(stories_table.c.source_author.in_(authors))
    if story_id is not None:
        query = query.where(stories_table.c.story_id == story_id)

    if sort_order == "source_story_id":
        query = query.order_by(
            stories_table.c.source_story_id.asc(),
            stories_table.c.source_author.asc(),
            stories_table.c.story_id.asc(),
        )
    else:
        query = query.order_by(stories_table.c.source_author.asc(), stories_table.c.story_id.asc())
    if limit is not None:
        query = query.limit(limit)

    rows = db.execute(query).mappings().all()
    return [_to_classical_story(row) for row in rows if _to_classical_story(row) is not None]


def update_classical_story_narration(
    db: Session,
    story_id: int,
    narration_payload: object,
) -> None:
    db.execute(
        update(stories_table)
        .where(stories_table.c.story_id == story_id)
        .values(narration=narration_payload)
    )


def update_classical_story_illustrations(
    db: Session,
    story_id: int,
    illustration_payload: object,
) -> None:
    db.execute(
        update(stories_table)
        .where(stories_table.c.story_id == story_id)
        .values(illustration_prompts=illustration_payload)
    )
