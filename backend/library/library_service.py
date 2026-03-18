import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.epub.epub_service import EpubService
from backend.epub.assets_manager import EpubAssetsManager
from backend.visuals.image_storage import IllustrationImageStorage
from backend.library.library_repository import (
    get_account_reader,
    get_reader_bookshelf,
    get_reader_library_story,
    list_reader_library_stories,
)


logger = logging.getLogger(__name__)
epub_assets_manager = EpubAssetsManager()
illustration_storage = IllustrationImageStorage()


class LibraryServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_identifier(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        raise LibraryServiceError(error_code="invalid_identifier", status_code=400)
    return value


def _resolve_reader_context(db: Session, account_id: int, reader_id: int):
    reader = get_account_reader(db, account_id, reader_id)
    if reader is None:
        raise LibraryServiceError(error_code="reader_not_found", status_code=404)

    bookshelf = get_reader_bookshelf(db, reader_id)
    if bookshelf is None:
        raise LibraryServiceError(error_code="library_not_found", status_code=404)

    return reader, bookshelf


def _serialize_library_story(story) -> dict[str, Any]:
    normalized_epub_url = epub_assets_manager.normalize_epub_url(story.story_id, story.epub_url)
    normalized_cover_image_url = illustration_storage.normalize_public_url(story.cover_image_url)
    return {
        "story_id": story.story_id,
        "title": story.title,
        "trait_focus": story.trait_focus,
        "current_version": story.current_version,
        "created_at": story.created_at,
        "updated_at": story.updated_at,
        "reader_world_id": story.reader_world_id,
        "world_id": story.world_id,
        "world_name": story.world_name,
        "custom_world_name": story.custom_world_name,
        "published": bool(normalized_epub_url),
        "epub_url": normalized_epub_url,
        "epub_created_at": story.epub_created_at,
        "cover_image_url": normalized_cover_image_url,
        "narration_available": story.narration_available,
        "artwork_available": story.artwork_available,
    }


def get_reader_library(db: Session, account_id: int, reader_id: Any) -> dict[str, Any]:
    normalized_reader_id = _validate_identifier(reader_id)
    logger.info(
        "reader library requested",
        extra={"account_id": account_id, "reader_id": normalized_reader_id},
    )

    try:
        reader, bookshelf = _resolve_reader_context(db, account_id, normalized_reader_id)
        stories = list_reader_library_stories(db, normalized_reader_id)
    except LibraryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader library lookup",
            extra={"account_id": account_id, "reader_id": normalized_reader_id},
        )
        raise LibraryServiceError(error_code="database_failure", status_code=500) from exc

    return {
        "reader_id": reader.reader_id,
        "reader_name": reader.name,
        "bookshelf_id": bookshelf.bookshelf_id,
        "bookshelf_created_at": bookshelf.created_at,
        "story_count": len(stories),
        "stories": [_serialize_library_story(story) for story in stories],
    }


def get_library_story_detail(
    db: Session,
    account_id: int,
    reader_id: Any,
    story_id: Any,
) -> dict[str, Any]:
    normalized_reader_id = _validate_identifier(reader_id)
    normalized_story_id = _validate_identifier(story_id)
    logger.info(
        "library story detail requested",
        extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
    )

    try:
        reader, bookshelf = _resolve_reader_context(db, account_id, normalized_reader_id)
        story = get_reader_library_story(db, normalized_reader_id, normalized_story_id)
        if story is None:
            raise LibraryServiceError(error_code="story_not_found", status_code=404)
    except LibraryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during library story detail lookup",
            extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
        )
        raise LibraryServiceError(error_code="database_failure", status_code=500) from exc

    return {
        "reader_id": reader.reader_id,
        "reader_name": reader.name,
        "bookshelf_id": bookshelf.bookshelf_id,
        "story": _serialize_library_story(story),
    }


def publish_library_story(
    db: Session,
    account_id: int,
    reader_id: Any,
    story_id: Any,
) -> dict[str, Any]:
    normalized_reader_id = _validate_identifier(reader_id)
    normalized_story_id = _validate_identifier(story_id)
    logger.info(
        "library publish requested",
        extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
    )

    try:
        _resolve_reader_context(db, account_id, normalized_reader_id)
        story = get_reader_library_story(db, normalized_reader_id, normalized_story_id)
        if story is None:
            raise LibraryServiceError(error_code="story_not_found", status_code=404)
    except LibraryServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure before publish",
            extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
        )
        raise LibraryServiceError(error_code="database_failure", status_code=500) from exc

    try:
        published = EpubService().export_story_epub(db, account_id, normalized_story_id)
        detail = get_reader_library_story(db, normalized_reader_id, normalized_story_id)
        if detail is None:
            raise LibraryServiceError(error_code="story_not_found", status_code=404)
    except LibraryServiceError:
        raise
    except HTTPException as exc:
        detail_code = "database_failure"
        if exc.status_code == 404:
            detail_code = "publish_asset_missing"
        logger.warning(
            "publish request failed in epub workflow",
            extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
        )
        raise LibraryServiceError(error_code=detail_code, status_code=exc.status_code) from exc
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during publish",
            extra={"account_id": account_id, "reader_id": normalized_reader_id, "story_id": normalized_story_id},
        )
        raise LibraryServiceError(error_code="database_failure", status_code=500) from exc

    return {
        "status": "published",
        "story_id": normalized_story_id,
        "epub_url": published["epub_url"],
        "story": _serialize_library_story(detail),
    }
