from dataclasses import dataclass

from sqlalchemy import Column, Integer, MetaData, String, Table, select
from sqlalchemy.orm import Session


metadata = MetaData()

vocabulary_table = Table(
    "vocabulary",
    metadata,
    Column("word_id", Integer, primary_key=True),
    Column("story_id", Integer),
    Column("word", String(100)),
    Column("difficulty_level", Integer),
)


@dataclass
class VocabularyRecord:
    word_id: int
    story_id: int | None
    word: str | None
    difficulty_level: int | None


def _to_vocabulary(row) -> VocabularyRecord | None:
    if row is None:
        return None
    return VocabularyRecord(
        word_id=row.word_id,
        story_id=row.story_id,
        word=row.word,
        difficulty_level=row.difficulty_level,
    )


def get_story_vocabulary_map(db: Session, story_id: int) -> dict[str, VocabularyRecord]:
    rows = db.execute(
        select(vocabulary_table).where(vocabulary_table.c.story_id == story_id)
    ).mappings().all()
    vocabulary_map: dict[str, VocabularyRecord] = {}
    for row in rows:
        vocabulary = _to_vocabulary(row)
        if vocabulary is not None and vocabulary.word:
            vocabulary_map[vocabulary.word] = vocabulary
    return vocabulary_map


def insert_story_vocabulary(
    db: Session,
    story_id: int,
    words: list[dict[str, int | str]],
) -> list[VocabularyRecord]:
    existing_map = get_story_vocabulary_map(db, story_id)

    for word_payload in words:
        word = word_payload["word"]
        if word in existing_map:
            continue
        result = db.execute(
            vocabulary_table.insert().values(
                story_id=story_id,
                word=word,
                difficulty_level=word_payload["difficulty_level"],
            )
        )
        existing_map[word] = VocabularyRecord(
            word_id=int(result.inserted_primary_key[0]),
            story_id=story_id,
            word=word,
            difficulty_level=int(word_payload["difficulty_level"]),
        )

    return list(existing_map.values())


def get_word_for_story(db: Session, story_id: int, word_id: int) -> VocabularyRecord | None:
    row = db.execute(
        select(vocabulary_table).where(
            (vocabulary_table.c.story_id == story_id) & (vocabulary_table.c.word_id == word_id)
        )
    ).mappings().first()
    return _to_vocabulary(row)
