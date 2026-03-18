import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from backend.classical_stories.chunking_service import build_story_chunks, write_chunks
from backend.classical_stories.destination_repository import get_existing_story_keys, insert_story
from backend.classical_stories.source_repository import fetch_story_batch
from backend.config.database_connections import (
    DestinationSessionLocal,
    SourceSessionLocal,
)


BATCH_SIZE = 50


@dataclass
class ImportSummary:
    total_processed: int = 0
    stories_imported: int = 0
    stories_skipped: int = 0


def run_import() -> ImportSummary:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = ImportSummary()
    chunk_rows: list[dict] = []
    offset = 0

    source_db = SourceSessionLocal()
    destination_db = DestinationSessionLocal()

    try:
        while True:
            batch = fetch_story_batch(source_db, offset=offset, limit=BATCH_SIZE)
            if not batch:
                break

            batch_keys = [
                (story.source_author, story.source_story_id)
                for story in batch
            ]
            existing_story_ids = get_existing_story_keys(destination_db, batch_keys)

            try:
                batch_imported = 0
                batch_skipped = 0

                for story in batch:
                    summary.total_processed += 1
                    logging.info("Processing story %s", story.story_id)

                    key = (story.source_author, story.source_story_id)
                    destination_story_id = existing_story_ids.get(key)

                    if destination_story_id is None:
                        destination_story_id = insert_story(destination_db, story)
                        existing_story_ids[key] = destination_story_id
                        summary.stories_imported += 1
                        batch_imported += 1
                    else:
                        summary.stories_skipped += 1
                        batch_skipped += 1

                    chunk_rows.extend(build_story_chunks(destination_story_id, story))

                destination_db.commit()
                logging.info("Imported %s stories", batch_imported)
                logging.info("Skipped %s duplicates", batch_skipped)
            except SQLAlchemyError:
                destination_db.rollback()
                raise

            offset += BATCH_SIZE

        write_chunks(chunk_rows)
        logging.info("total_processed: %s", summary.total_processed)
        logging.info("stories_imported: %s", summary.stories_imported)
        logging.info("stories_skipped: %s", summary.stories_skipped)
        return summary
    finally:
        source_db.close()
        destination_db.close()


if __name__ == "__main__":
    run_import()
