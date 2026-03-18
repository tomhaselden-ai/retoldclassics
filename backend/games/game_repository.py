import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, and_, desc, literal, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

readers_table = Table(
    "readers",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("name", String(100)),
    Column("reading_level", String(50)),
)

reader_vocabulary_progress_table = Table(
    "reader_vocabulary_progress",
    metadata,
    Column("reader_id", Integer, primary_key=True),
    Column("word_id", Integer, primary_key=True),
    Column("mastery_level", Integer),
    Column("last_seen", DateTime),
)

vocabulary_table = Table(
    "vocabulary",
    metadata,
    Column("word_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("word", String(100)),
    Column("difficulty_level", Integer),
)

game_results_table = Table(
    "game_results",
    metadata,
    Column("game_result_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("game_type", String(50)),
    Column("difficulty_level", Integer),
    Column("score", Integer),
    Column("duration_seconds", Integer),
    Column("played_at", DateTime),
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
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

reader_worlds_table = Table(
    "reader_worlds",
    metadata,
    Column("reader_world_id", Integer, primary_key=True),
    Column("reader_id", Integer),
    Column("world_id", Integer),
    Column("custom_name", String(255)),
    Column("created_at", DateTime),
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
    Column("characters", JSON),
    Column("location_id", Integer),
    Column("event_summary", Text),
)

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
)

characters_table = Table(
    "characters",
    metadata,
    Column("character_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("species", String(100)),
    Column("personality_traits", JSON),
    Column("home_location", Integer),
    Column("updated_at", DateTime),
)


@dataclass
class ReaderRecord:
    reader_id: int
    account_id: int
    name: str | None
    reading_level: str | None


@dataclass
class VocabularyRecord:
    word_id: int
    word: str | None
    difficulty_level: int | None
    mastery_level: int | None
    last_seen: datetime | None


@dataclass
class StoryRecord:
    story_id: int
    reader_id: int | None
    reader_world_id: int | None
    world_id: int | None
    title: str | None
    created_at: datetime | None


@dataclass
class StoryEventRecord:
    event_id: int
    story_id: int | None
    characters: list[int]
    location_id: int | None
    location_name: str | None
    event_summary: str | None


@dataclass
class CharacterRecord:
    character_id: int
    name: str | None


@dataclass
class GameResultRecord:
    game_result_id: int
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


def _parse_character_ids(value) -> list[int]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, int)]
    return []


def _to_reader(row) -> ReaderRecord | None:
    if row is None:
        return None
    return ReaderRecord(
        reader_id=row.reader_id,
        account_id=row.account_id,
        name=row.name,
        reading_level=row.reading_level,
    )


def _to_vocabulary(row) -> VocabularyRecord | None:
    if row is None:
        return None
    return VocabularyRecord(
        word_id=row.word_id,
        word=row.word,
        difficulty_level=row.difficulty_level,
        mastery_level=row.mastery_level,
        last_seen=row.last_seen,
    )


def _to_story(row) -> StoryRecord | None:
    if row is None:
        return None
    return StoryRecord(
        story_id=row.story_id,
        reader_id=row.reader_id,
        reader_world_id=row.reader_world_id,
        world_id=row.world_id,
        title=row.title,
        created_at=row.created_at,
    )


def _to_story_event(row) -> StoryEventRecord | None:
    if row is None:
        return None
    return StoryEventRecord(
        event_id=row.event_id,
        story_id=row.story_id,
        characters=_parse_character_ids(row.characters),
        location_id=row.location_id,
        location_name=row.location_name,
        event_summary=row.event_summary,
    )


def _to_character(row) -> CharacterRecord | None:
    if row is None:
        return None
    return CharacterRecord(
        character_id=row.character_id,
        name=row.name,
    )


def _to_game_result(row) -> GameResultRecord | None:
    if row is None:
        return None
    return GameResultRecord(
        game_result_id=row.game_result_id,
        game_type=row.game_type,
        difficulty_level=row.difficulty_level,
        score=row.score,
        duration_seconds=row.duration_seconds,
        played_at=row.played_at,
    )


def get_reader_for_account(db: Session, reader_id: int, account_id: int) -> ReaderRecord | None:
    row = db.execute(
        select(readers_table).where(
            and_(
                readers_table.c.reader_id == reader_id,
                readers_table.c.account_id == account_id,
            )
        )
    ).mappings().first()
    return _to_reader(row)


def list_reader_practice_vocabulary(
    db: Session,
    reader_id: int,
    max_difficulty: int,
    limit: int,
) -> list[VocabularyRecord]:
    rows = db.execute(
        select(
            vocabulary_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.difficulty_level,
            reader_vocabulary_progress_table.c.mastery_level,
            reader_vocabulary_progress_table.c.last_seen,
        )
        .select_from(
            reader_vocabulary_progress_table.join(
                vocabulary_table,
                reader_vocabulary_progress_table.c.word_id == vocabulary_table.c.word_id,
            )
        )
        .where(
            and_(
                reader_vocabulary_progress_table.c.reader_id == reader_id,
                vocabulary_table.c.difficulty_level <= max_difficulty,
            )
        )
        .order_by(
            reader_vocabulary_progress_table.c.mastery_level.asc(),
            desc(reader_vocabulary_progress_table.c.last_seen),
            vocabulary_table.c.word.asc(),
        )
        .limit(limit)
    ).mappings().all()
    return [_to_vocabulary(row) for row in rows if _to_vocabulary(row) is not None]


def list_reader_story_vocabulary(
    db: Session,
    reader_id: int,
    max_difficulty: int,
    limit: int,
) -> list[VocabularyRecord]:
    rows = db.execute(
        select(
            vocabulary_table.c.word_id,
            vocabulary_table.c.word,
            vocabulary_table.c.difficulty_level,
            literal(None).label("mastery_level"),
            literal(None).label("last_seen"),
        )
        .select_from(
            vocabulary_table.join(
                stories_generated_table,
                vocabulary_table.c.story_id == stories_generated_table.c.story_id,
            )
        )
        .where(
            and_(
                stories_generated_table.c.reader_id == reader_id,
                vocabulary_table.c.difficulty_level <= max_difficulty,
            )
        )
        .order_by(desc(stories_generated_table.c.created_at), vocabulary_table.c.word.asc())
        .limit(limit)
    ).mappings().all()
    return [_to_vocabulary(row) for row in rows if _to_vocabulary(row) is not None]


def list_global_vocabulary_words(
    db: Session,
    exclude_word_ids: list[int],
    limit: int,
) -> list[str]:
    query = select(vocabulary_table.c.word).where(vocabulary_table.c.word.is_not(None))
    if exclude_word_ids:
        query = query.where(vocabulary_table.c.word_id.notin_(exclude_word_ids))
    rows = db.execute(query.order_by(vocabulary_table.c.word.asc()).limit(limit)).all()
    return [row.word for row in rows if row.word]


def get_story_for_reader(db: Session, reader_id: int, story_id: int) -> StoryRecord | None:
    row = db.execute(
        select(
            stories_generated_table.c.story_id,
            stories_generated_table.c.reader_id,
            stories_generated_table.c.reader_world_id,
            reader_worlds_table.c.world_id,
            stories_generated_table.c.title,
            stories_generated_table.c.created_at,
        )
        .select_from(
            stories_generated_table.join(
                reader_worlds_table,
                stories_generated_table.c.reader_world_id == reader_worlds_table.c.reader_world_id,
            )
        )
        .where(
            and_(
                stories_generated_table.c.reader_id == reader_id,
                stories_generated_table.c.story_id == story_id,
            )
        )
    ).mappings().first()
    return _to_story(row)


def get_latest_story_for_reader(db: Session, reader_id: int) -> StoryRecord | None:
    row = db.execute(
        select(
            stories_generated_table.c.story_id,
            stories_generated_table.c.reader_id,
            stories_generated_table.c.reader_world_id,
            reader_worlds_table.c.world_id,
            stories_generated_table.c.title,
            stories_generated_table.c.created_at,
        )
        .select_from(
            stories_generated_table.join(
                reader_worlds_table,
                stories_generated_table.c.reader_world_id == reader_worlds_table.c.reader_world_id,
            )
        )
        .where(stories_generated_table.c.reader_id == reader_id)
        .order_by(desc(stories_generated_table.c.created_at), desc(stories_generated_table.c.story_id))
        .limit(1)
    ).mappings().first()
    return _to_story(row)


def list_story_scene_payloads(db: Session, story_id: int) -> list[dict]:
    rows = db.execute(
        select(story_scenes_table.c.scene_text)
        .where(story_scenes_table.c.story_id == story_id)
        .order_by(story_scenes_table.c.scene_order.asc(), story_scenes_table.c.scene_id.asc())
    ).all()

    scene_payloads: list[dict] = []
    for row in rows:
        if not isinstance(row.scene_text, str) or not row.scene_text.strip():
            continue
        try:
            payload = json.loads(row.scene_text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            scene_payloads.append(payload)
    return scene_payloads


def list_story_events(db: Session, story_id: int) -> list[StoryEventRecord]:
    rows = db.execute(
        select(
            story_events_table.c.event_id,
            story_events_table.c.story_id,
            story_events_table.c.characters,
            story_events_table.c.location_id,
            locations_table.c.name.label("location_name"),
            story_events_table.c.event_summary,
        )
        .select_from(
            story_events_table.outerjoin(
                locations_table,
                story_events_table.c.location_id == locations_table.c.location_id,
            )
        )
        .where(story_events_table.c.story_id == story_id)
        .order_by(story_events_table.c.event_id.asc())
    ).mappings().all()
    return [_to_story_event(row) for row in rows if _to_story_event(row) is not None]


def list_other_story_event_summaries(
    db: Session,
    exclude_story_id: int,
    limit: int,
) -> list[str]:
    rows = db.execute(
        select(story_events_table.c.event_summary)
        .where(
            and_(
                story_events_table.c.story_id != exclude_story_id,
                story_events_table.c.event_summary.is_not(None),
            )
        )
        .order_by(desc(story_events_table.c.event_id))
        .limit(limit)
    ).all()
    return [row.event_summary for row in rows if row.event_summary]


def list_characters_by_ids(db: Session, character_ids: list[int]) -> list[CharacterRecord]:
    if not character_ids:
        return []
    rows = db.execute(
        select(characters_table.c.character_id, characters_table.c.name)
        .where(characters_table.c.character_id.in_(character_ids))
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()
    return [_to_character(row) for row in rows if _to_character(row) is not None]


def list_other_character_names(
    db: Session,
    exclude_character_ids: list[int],
    limit: int,
) -> list[str]:
    query = select(characters_table.c.name).where(characters_table.c.name.is_not(None))
    if exclude_character_ids:
        query = query.where(characters_table.c.character_id.notin_(exclude_character_ids))
    rows = db.execute(query.order_by(characters_table.c.name.asc()).limit(limit)).all()
    return [row.name for row in rows if row.name]


def list_reader_game_results(db: Session, reader_id: int, limit: int = 20) -> list[GameResultRecord]:
    rows = db.execute(
        select(game_results_table)
        .where(game_results_table.c.reader_id == reader_id)
        .order_by(desc(game_results_table.c.played_at), desc(game_results_table.c.game_result_id))
        .limit(limit)
    ).mappings().all()
    return [_to_game_result(row) for row in rows if _to_game_result(row) is not None]


def insert_game_result(
    db: Session,
    reader_id: int,
    game_type: str,
    difficulty_level: int,
    score: int,
    duration_seconds: int,
) -> int:
    result = db.execute(
        game_results_table.insert().values(
            reader_id=reader_id,
            game_type=game_type,
            difficulty_level=difficulty_level,
            score=score,
            duration_seconds=duration_seconds,
        )
    )
    return int(result.inserted_primary_key[0])
