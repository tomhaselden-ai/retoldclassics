from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, case, desc, exists, func, select
from sqlalchemy.orm import Session


metadata = MetaData()

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

bookshelves_table = Table(
    "bookshelves",
    metadata,
    Column("bookshelf_id", Integer, primary_key=True),
    Column("reader_id", Integer, nullable=False),
    Column("created_at", TIMESTAMP),
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

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
    Column("updated_at", TIMESTAMP),
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

epub_books_table = Table(
    "epub_books",
    metadata,
    Column("epub_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("epub_url", Text),
    Column("created_at", TIMESTAMP),
)

story_scenes_table = Table(
    "story_scenes",
    metadata,
    Column("scene_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("scene_order", Integer),
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
)

illustrations_table = Table(
    "illustrations",
    metadata,
    Column("illustration_id", Integer, primary_key=True),
    Column("scene_id", Integer),
    Column("image_url", Text),
)


@dataclass
class ReaderRecord:
    reader_id: int
    account_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    gender_preference: str | None
    created_at: datetime | None


@dataclass
class BookshelfRecord:
    bookshelf_id: int
    reader_id: int
    created_at: datetime | None


@dataclass
class LibraryStoryRecord:
    story_id: int
    reader_id: int | None
    reader_world_id: int | None
    title: str | None
    trait_focus: str | None
    current_version: int | None
    created_at: datetime | None
    updated_at: datetime | None
    world_id: int | None
    world_name: str | None
    custom_world_name: str | None
    epub_url: str | None
    epub_created_at: datetime | None
    cover_image_url: str | None
    narration_available: bool
    artwork_available: bool


def _to_reader(row) -> ReaderRecord | None:
    if row is None:
        return None
    return ReaderRecord(
        reader_id=row.reader_id,
        account_id=row.account_id,
        name=row.name,
        age=row.age,
        reading_level=row.reading_level,
        gender_preference=row.gender_preference,
        created_at=row.created_at,
    )


def _to_bookshelf(row) -> BookshelfRecord | None:
    if row is None:
        return None
    return BookshelfRecord(
        bookshelf_id=row.bookshelf_id,
        reader_id=row.reader_id,
        created_at=row.created_at,
    )


def _to_library_story(row) -> LibraryStoryRecord | None:
    if row is None:
        return None
    return LibraryStoryRecord(
        story_id=row.story_id,
        reader_id=row.reader_id,
        reader_world_id=row.reader_world_id,
        title=row.title,
        trait_focus=row.trait_focus,
        current_version=row.current_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
        world_id=row.world_id,
        world_name=row.world_name,
        custom_world_name=row.custom_world_name,
        epub_url=row.epub_url,
        epub_created_at=row.epub_created_at,
        cover_image_url=row.cover_image_url,
        narration_available=bool(row.narration_available),
        artwork_available=bool(row.artwork_available),
    )


def _library_story_query():
    cover_from_illustrations = (
        select(illustrations_table.c.image_url)
        .select_from(
            story_scenes_table.join(
                illustrations_table,
                story_scenes_table.c.scene_id == illustrations_table.c.scene_id,
            )
        )
        .where(
            and_(
                story_scenes_table.c.story_id == stories_generated_table.c.story_id,
                illustrations_table.c.image_url.isnot(None),
            )
        )
        .order_by(story_scenes_table.c.scene_order.asc(), illustrations_table.c.illustration_id.asc())
        .limit(1)
        .scalar_subquery()
    )

    cover_from_scene = (
        select(story_scenes_table.c.illustration_url)
        .where(
            and_(
                story_scenes_table.c.story_id == stories_generated_table.c.story_id,
                story_scenes_table.c.illustration_url.isnot(None),
            )
        )
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
        .limit(1)
        .scalar_subquery()
    )

    narration_exists = exists(
        select(1).where(
            and_(
                narration_audio_table.c.story_id == stories_generated_table.c.story_id,
                narration_audio_table.c.audio_url.isnot(None),
            )
        )
    )

    scene_audio_exists = exists(
        select(1).where(
            and_(
                story_scenes_table.c.story_id == stories_generated_table.c.story_id,
                story_scenes_table.c.audio_url.isnot(None),
            )
        )
    )

    artwork_exists = exists(
        select(1)
        .select_from(
            story_scenes_table.outerjoin(
                illustrations_table,
                story_scenes_table.c.scene_id == illustrations_table.c.scene_id,
            )
        )
        .where(
            and_(
                story_scenes_table.c.story_id == stories_generated_table.c.story_id,
                func.coalesce(illustrations_table.c.image_url, story_scenes_table.c.illustration_url).isnot(None),
            )
        )
    )

    return select(
        stories_generated_table.c.story_id,
        stories_generated_table.c.reader_id,
        stories_generated_table.c.reader_world_id,
        stories_generated_table.c.title,
        stories_generated_table.c.trait_focus,
        stories_generated_table.c.current_version,
        stories_generated_table.c.created_at,
        stories_generated_table.c.updated_at,
        reader_worlds_table.c.world_id,
        worlds_table.c.name.label("world_name"),
        reader_worlds_table.c.custom_name.label("custom_world_name"),
        epub_books_table.c.epub_url,
        epub_books_table.c.created_at.label("epub_created_at"),
        func.coalesce(cover_from_illustrations, cover_from_scene).label("cover_image_url"),
        case((narration_exists, True), (scene_audio_exists, True), else_=False).label("narration_available"),
        case((artwork_exists, True), else_=False).label("artwork_available"),
    ).select_from(
        stories_generated_table.outerjoin(
            reader_worlds_table,
            stories_generated_table.c.reader_world_id == reader_worlds_table.c.reader_world_id,
        )
        .outerjoin(
            worlds_table,
            reader_worlds_table.c.world_id == worlds_table.c.world_id,
        )
        .outerjoin(
            epub_books_table,
            stories_generated_table.c.story_id == epub_books_table.c.story_id,
        )
    )


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


def get_reader_bookshelf(db: Session, reader_id: int) -> BookshelfRecord | None:
    row = db.execute(
        select(bookshelves_table)
        .where(bookshelves_table.c.reader_id == reader_id)
        .order_by(bookshelves_table.c.bookshelf_id.asc())
    ).mappings().first()
    return _to_bookshelf(row)


def list_reader_library_stories(db: Session, reader_id: int) -> list[LibraryStoryRecord]:
    rows = db.execute(
        _library_story_query()
        .where(stories_generated_table.c.reader_id == reader_id)
        .order_by(desc(stories_generated_table.c.updated_at), desc(stories_generated_table.c.story_id))
    ).mappings().all()
    return [_to_library_story(row) for row in rows if _to_library_story(row) is not None]


def get_reader_library_story(db: Session, reader_id: int, story_id: int) -> LibraryStoryRecord | None:
    row = db.execute(
        _library_story_query()
        .where(
            and_(
                stories_generated_table.c.reader_id == reader_id,
                stories_generated_table.c.story_id == story_id,
            )
        )
    ).mappings().first()
    return _to_library_story(row)
