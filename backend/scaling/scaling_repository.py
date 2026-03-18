from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, desc, func, select
from sqlalchemy.orm import Session


metadata = MetaData()

accounts_table = Table(
    "accounts",
    metadata,
    Column("account_id", Integer, primary_key=True),
    Column("email", String(255)),
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
    Column("created_at", TIMESTAMP),
)

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
    Column("updated_at", TIMESTAMP),
)

reader_worlds_table = Table(
    "reader_worlds",
    metadata,
    Column("reader_world_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("world_id", Integer),
    Column("custom_name", String(255)),
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

story_events_table = Table(
    "story_events",
    metadata,
    Column("event_id", Integer, primary_key=True),
    Column("story_id", Integer),
)

vector_memory_index_table = Table(
    "vector_memory_index",
    metadata,
    Column("vector_id", String(128), primary_key=True),
    Column("source_type", String(50)),
    Column("source_id", Integer),
    Column("created_at", TIMESTAMP),
)


@dataclass
class AccountRecord:
    account_id: int
    email: str | None
    subscription_level: str | None
    story_security: str | None
    created_at: datetime | None


@dataclass
class ReaderRecord:
    reader_id: int
    account_id: int
    name: str | None
    reading_level: str | None


@dataclass
class WorldRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None
    updated_at: datetime | None


@dataclass
class ReaderWorldRecord:
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
    custom_name: str | None
    created_at: datetime | None
    world_name: str | None
    world_default_world: bool | None


def _to_account(row) -> AccountRecord | None:
    if row is None:
        return None
    return AccountRecord(
        account_id=row.account_id,
        email=row.email,
        subscription_level=row.subscription_level,
        story_security=row.story_security,
        created_at=row.created_at,
    )


def _to_reader(row) -> ReaderRecord | None:
    if row is None:
        return None
    return ReaderRecord(
        reader_id=row.reader_id,
        account_id=row.account_id,
        name=row.name,
        reading_level=row.reading_level,
    )


def _to_world(row) -> WorldRecord | None:
    if row is None:
        return None
    return WorldRecord(
        world_id=row.world_id,
        name=row.name,
        description=row.description,
        default_world=bool(row.default_world) if row.default_world is not None else None,
        updated_at=row.updated_at,
    )


def _to_reader_world(row) -> ReaderWorldRecord | None:
    if row is None:
        return None
    return ReaderWorldRecord(
        reader_world_id=row.reader_world_id,
        reader_id=row.reader_id,
        world_id=row.world_id,
        custom_name=row.custom_name,
        created_at=row.created_at,
        world_name=row.world_name,
        world_default_world=bool(row.world_default_world) if row.world_default_world is not None else None,
    )


def get_account(db: Session, account_id: int) -> AccountRecord | None:
    row = db.execute(
        select(accounts_table).where(accounts_table.c.account_id == account_id)
    ).mappings().first()
    return _to_account(row)


def get_account_reader(db: Session, account_id: int, reader_id: int) -> ReaderRecord | None:
    row = db.execute(
        select(readers_table).where(
            and_(
                readers_table.c.account_id == account_id,
                readers_table.c.reader_id == reader_id,
            )
        )
    ).mappings().first()
    return _to_reader(row)


def count_account_readers(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count()).select_from(readers_table).where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)


def count_account_assigned_worlds(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count())
        .select_from(
            reader_worlds_table.join(readers_table, reader_worlds_table.c.reader_id == readers_table.c.reader_id)
        )
        .where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)


def count_account_generated_stories(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count())
        .select_from(
            stories_generated_table.join(readers_table, stories_generated_table.c.reader_id == readers_table.c.reader_id)
        )
        .where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)


def count_worlds(db: Session) -> int:
    value = db.execute(select(func.count()).select_from(worlds_table)).scalar_one()
    return int(value or 0)


def count_default_worlds(db: Session) -> int:
    value = db.execute(
        select(func.count()).select_from(worlds_table).where(worlds_table.c.default_world == 1)
    ).scalar_one()
    return int(value or 0)


def list_worlds(db: Session, limit: int, offset: int) -> list[WorldRecord]:
    rows = db.execute(
        select(worlds_table)
        .order_by(worlds_table.c.world_id.asc())
        .offset(offset)
        .limit(limit)
    ).mappings().all()
    return [_to_world(row) for row in rows if _to_world(row) is not None]


def list_reader_world_assignments(db: Session, reader_id: int) -> list[ReaderWorldRecord]:
    rows = db.execute(
        select(
            reader_worlds_table.c.reader_world_id,
            reader_worlds_table.c.reader_id,
            reader_worlds_table.c.world_id,
            reader_worlds_table.c.custom_name,
            reader_worlds_table.c.created_at,
            worlds_table.c.name.label("world_name"),
            worlds_table.c.default_world.label("world_default_world"),
        )
        .select_from(
            reader_worlds_table.join(worlds_table, reader_worlds_table.c.world_id == worlds_table.c.world_id)
        )
        .where(reader_worlds_table.c.reader_id == reader_id)
        .order_by(desc(reader_worlds_table.c.created_at), desc(reader_worlds_table.c.reader_world_id))
    ).mappings().all()
    return [_to_reader_world(row) for row in rows if _to_reader_world(row) is not None]


def count_account_story_events(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count())
        .select_from(
            story_events_table.join(
                stories_generated_table,
                story_events_table.c.story_id == stories_generated_table.c.story_id,
            ).join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)


def count_account_indexed_story_events(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count())
        .select_from(
            story_events_table.join(
                stories_generated_table,
                story_events_table.c.story_id == stories_generated_table.c.story_id,
            ).join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            ).join(
                vector_memory_index_table,
                and_(
                    vector_memory_index_table.c.source_type == "story_event",
                    vector_memory_index_table.c.source_id == story_events_table.c.event_id,
                ),
            )
        )
        .where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)


def count_account_index_rows(db: Session, account_id: int) -> int:
    value = db.execute(
        select(func.count())
        .select_from(
            vector_memory_index_table.join(
                story_events_table,
                and_(
                    vector_memory_index_table.c.source_type == "story_event",
                    vector_memory_index_table.c.source_id == story_events_table.c.event_id,
                ),
            ).join(
                stories_generated_table,
                story_events_table.c.story_id == stories_generated_table.c.story_id,
            ).join(
                readers_table,
                stories_generated_table.c.reader_id == readers_table.c.reader_id,
            )
        )
        .where(readers_table.c.account_id == account_id)
    ).scalar_one()
    return int(value or 0)
