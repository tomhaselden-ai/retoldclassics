import logging

from sqlalchemy.orm import Session

from backend.reader.scene_repository import get_story_scenes
from backend.vocabulary.progress_repository import (
    ensure_reader_vocabulary_progress,
    get_practice_vocabulary,
    get_reader_for_account,
    list_reader_vocabulary,
    sync_reader_progress_metrics,
    update_reader_word_progress,
)
from backend.vocabulary.vocabulary_extractor import extract_vocabulary_words
from backend.vocabulary.vocabulary_repository import get_word_for_story, insert_story_vocabulary


def extract_story_vocabulary(db: Session, reader_id: int, story_id: int, reading_level: str | None) -> None:
    logging.info("Extracting vocabulary for story %s", story_id)
    scenes = get_story_scenes(db, story_id)
    scene_texts = [scene.scene_text or "" for scene in scenes]
    words = extract_vocabulary_words(scene_texts, reading_level)
    vocabulary_records = insert_story_vocabulary(db, story_id, words)
    ensure_reader_vocabulary_progress(
        db,
        reader_id,
        [record.word_id for record in vocabulary_records],
    )
    sync_reader_progress_metrics(db, reader_id)


def get_reader_vocabulary(db: Session, account_id: int, reader_id: int) -> list[dict]:
    get_reader_for_account(db, reader_id, account_id)
    return list_reader_vocabulary(db, reader_id)


def update_vocabulary_progress(
    db: Session,
    account_id: int,
    reader_id: int,
    word_id: int,
    mastery_level: int,
) -> dict:
    get_reader_for_account(db, reader_id, account_id)
    progress = update_reader_word_progress(db, reader_id, word_id, mastery_level)
    sync_reader_progress_metrics(db, reader_id)
    db.commit()
    return {
        "word_id": progress.word_id,
        "mastery_level": progress.mastery_level,
        "last_seen": progress.last_seen,
    }


def get_reader_practice_vocabulary(db: Session, account_id: int, reader_id: int) -> list[dict]:
    get_reader_for_account(db, reader_id, account_id)
    return get_practice_vocabulary(db, reader_id)
