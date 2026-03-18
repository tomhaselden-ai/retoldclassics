import argparse
import logging

from backend.classics.classics_narration_service import generate_classics_narration
from backend.classics.classics_repository import ClassicalStoryRecord
from backend.classics.classics_serializer import ALLOWED_AUTHORS
from backend.db.database import SessionLocal
from backend.narration.polly_client import DEFAULT_VOICE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate classics narration and illustrations for classical stories.")
    parser.add_argument("--author", choices=ALLOWED_AUTHORS, default=None)
    parser.add_argument("--story-id", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sort", choices=["author", "source_story_id"], default="source_story_id")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    return parser.parse_args()


def log_story_progress(story: ClassicalStoryRecord, status: str) -> None:
    author = story.source_author or "Unknown author"
    title = story.title or f"Story {story.story_id}"
    logging.info("%s: %s - %s", status, author, title)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    db = SessionLocal()

    try:
        summary = generate_classics_narration(
            db=db,
            author=args.author,
            story_id=args.story_id,
            limit=args.limit,
            sort_order=args.sort,
            force=args.force,
            voice=args.voice,
            progress_callback=log_story_progress,
        )
        logging.info("processed: %s", summary.processed)
        logging.info("generated: %s", summary.generated)
        logging.info("skipped: %s", summary.skipped)
        logging.info("narration generated: %s", summary.narration_generated)
        logging.info("illustrations generated: %s", summary.illustrations_generated)
    finally:
        db.close()


if __name__ == "__main__":
    main()
