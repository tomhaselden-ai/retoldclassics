from sqlalchemy import (
    JSON,
    FLOAT,
    Column,
    Integer,
    MetaData,
    String,
    TIMESTAMP,
    Table,
)


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
    Column("trait_focus", JSON),
    Column("created_at", TIMESTAMP),
)

bookshelves_table = Table(
    "bookshelves",
    metadata,
    Column("bookshelf_id", Integer, primary_key=True),
    Column("reader_id", Integer, nullable=False),
    Column("created_at", TIMESTAMP),
)

reader_progress_table = Table(
    "reader_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("stories_read", Integer),
    Column("words_mastered", Integer),
    Column("reading_speed", FLOAT),
    Column("preferred_themes", JSON),
    Column("traits_reinforced", JSON),
)
