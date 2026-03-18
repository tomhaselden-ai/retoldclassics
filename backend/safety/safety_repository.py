from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, select
from sqlalchemy.orm import Session


metadata = MetaData()

accounts_table = Table(
    "accounts",
    metadata,
    Column("account_id", Integer, primary_key=True),
    Column("email", String(255)),
    Column("password_hash", String(255)),
    Column("subscription_level", String(50)),
    Column("story_security", String(50)),
    Column("created_at", TIMESTAMP),
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
    Column("trait_focus", Text),
    Column("created_at", TIMESTAMP),
)

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

story_events_table = Table(
    "story_events",
    metadata,
    Column("event_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("characters", Text),
    Column("location_id", Integer),
    Column("event_summary", Text),
)


@dataclass
class AccountPolicyRecord:
    account_id: int
    story_security: str | None


@dataclass
class StoryRecord:
    story_id: int
    reader_id: int | None
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
class StoryEventRecord:
    event_id: int
    story_id: int | None
    event_summary: str | None


def _to_account_policy(row) -> AccountPolicyRecord | None:
    if row is None:
        return None
    return AccountPolicyRecord(
        account_id=row.account_id,
        story_security=row.story_security,
    )


def _to_story(row) -> StoryRecord | None:
    if row is None:
        return None
    return StoryRecord(
        story_id=row.story_id,
        reader_id=row.reader_id,
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


def _to_story_event(row) -> StoryEventRecord | None:
    if row is None:
        return None
    return StoryEventRecord(
        event_id=row.event_id,
        story_id=row.story_id,
        event_summary=row.event_summary,
    )


def get_account_policy(db: Session, account_id: int) -> AccountPolicyRecord | None:
    row = db.execute(
        select(accounts_table.c.account_id, accounts_table.c.story_security)
        .where(accounts_table.c.account_id == account_id)
    ).mappings().first()
    return _to_account_policy(row)


def get_story_for_account(db: Session, account_id: int, story_id: int) -> StoryRecord:
    row = db.execute(
        select(
            stories_generated_table.c.story_id,
            stories_generated_table.c.reader_id,
            stories_generated_table.c.title,
            stories_generated_table.c.trait_focus,
            stories_generated_table.c.current_version,
            stories_generated_table.c.created_at,
            stories_generated_table.c.updated_at,
        )
        .select_from(
            stories_generated_table.join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(
            and_(
                readers_table.c.account_id == account_id,
                stories_generated_table.c.story_id == story_id,
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


def list_story_scenes(db: Session, story_id: int) -> list[SceneRecord]:
    rows = db.execute(
        select(story_scenes_table)
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
    ).mappings().all()
    return [_to_scene(row) for row in rows if _to_scene(row) is not None]


def get_story_scene(db: Session, story_id: int, scene_id: int) -> SceneRecord:
    row = db.execute(
        select(story_scenes_table).where(
            and_(
                story_scenes_table.c.story_id == story_id,
                story_scenes_table.c.scene_id == scene_id,
            )
        )
    ).mappings().first()
    scene = _to_scene(row)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )
    return scene


def list_story_events(db: Session, story_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(story_events_table.c.event_id, story_events_table.c.story_id, story_events_table.c.event_summary)
        .where(story_events_table.c.story_id == story_id)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    return [_to_story_event(row) for row in rows if _to_story_event(row) is not None]
