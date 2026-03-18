import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.classics.classics_repository import (
    count_classical_stories,
    get_classical_story,
    list_classical_stories,
)
from backend.classics.classics_semantic_search_service import discover_classics
from backend.classics.classics_serializer import (
    ALLOWED_AUTHORS,
    build_read_payload,
    build_shelf_payload,
    build_story_detail_payload,
    expand_author_filters,
    normalize_author,
)


logger = logging.getLogger(__name__)


class ClassicsServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_limit_offset(limit: Any, offset: Any) -> tuple[int, int]:
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ClassicsServiceError(error_code="invalid_input", status_code=400)
    if not isinstance(offset, int) or offset < 0:
        raise ClassicsServiceError(error_code="invalid_input", status_code=400)
    return limit, offset


def _validate_story_id(story_id: Any) -> int:
    if not isinstance(story_id, int) or story_id <= 0:
        raise ClassicsServiceError(error_code="invalid_identifier", status_code=400)
    return story_id


def _resolve_authors(author: Any | None) -> list[str]:
    if author is None:
        return expand_author_filters(list(ALLOWED_AUTHORS))
    if not isinstance(author, str):
        raise ClassicsServiceError(error_code="invalid_input", status_code=400)
    normalized = normalize_author(author)
    if normalized is None:
        raise ClassicsServiceError(error_code="invalid_input", status_code=400)
    return expand_author_filters([normalized])


def get_classics_shelf(
    db: Session,
    author: Any | None = None,
    q: Any | None = None,
    limit: Any = 40,
    offset: Any = 0,
) -> dict[str, Any]:
    authors = _resolve_authors(author)
    normalized_limit, normalized_offset = _validate_limit_offset(limit, offset)
    query_text = q.strip() if isinstance(q, str) and q.strip() else None

    logger.info("classics shelf requested", extra={"author": author, "limit": normalized_limit, "offset": normalized_offset})

    try:
        stories = list_classical_stories(db, authors, query_text, normalized_limit, normalized_offset)
        total_count = count_classical_stories(db, authors, query_text)
        payload = build_shelf_payload(stories, total_count)
        payload["limit"] = normalized_limit
        payload["offset"] = normalized_offset
        return payload
    except ClassicsServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during classics shelf lookup")
        raise ClassicsServiceError(error_code="database_failure", status_code=500) from exc


def get_classics_discovery(
    db: Session,
    author: Any | None = None,
    q: Any | None = None,
    limit: Any = 24,
    offset: Any = 0,
) -> dict[str, Any]:
    authors = _resolve_authors(author)
    normalized_limit, normalized_offset = _validate_limit_offset(limit, offset)
    query_text = q.strip() if isinstance(q, str) and q.strip() else None
    applied_author = normalize_author(author) if isinstance(author, str) and author.strip() else None

    logger.info(
        "classics discovery requested",
        extra={"author": applied_author, "limit": normalized_limit, "offset": normalized_offset, "query": query_text},
    )

    try:
        return discover_classics(
            db,
            authors=authors,
            query_text=query_text,
            limit=normalized_limit,
            offset=normalized_offset,
            applied_author=applied_author,
        )
    except SQLAlchemyError as exc:
        logger.exception("database failure during classics discovery lookup")
        raise ClassicsServiceError(error_code="database_failure", status_code=500) from exc


def get_classic_story_detail(db: Session, story_id: Any) -> dict[str, Any]:
    normalized_story_id = _validate_story_id(story_id)
    logger.info("classic story detail requested", extra={"story_id": normalized_story_id})

    try:
        story = get_classical_story(db, normalized_story_id, expand_author_filters(list(ALLOWED_AUTHORS)))
        if story is None:
            raise ClassicsServiceError(error_code="story_not_found", status_code=404)
        return build_story_detail_payload(story)
    except ClassicsServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("database failure during classic story detail lookup", extra={"story_id": normalized_story_id})
        raise ClassicsServiceError(error_code="database_failure", status_code=500) from exc


def get_classic_story_read_payload(db: Session, story_id: Any) -> dict[str, Any]:
    normalized_story_id = _validate_story_id(story_id)
    logger.info("classic story read requested", extra={"story_id": normalized_story_id})

    try:
        story = get_classical_story(db, normalized_story_id, expand_author_filters(list(ALLOWED_AUTHORS)))
        if story is None:
            raise ClassicsServiceError(error_code="story_not_found", status_code=404)
        return build_read_payload(story)
    except ClassicsServiceError:
        raise
    except ValueError as exc:
        raise ClassicsServiceError(error_code="unreadable_story", status_code=500) from exc
    except SQLAlchemyError as exc:
        logger.exception("database failure during classic story read lookup", extra={"story_id": normalized_story_id})
        raise ClassicsServiceError(error_code="database_failure", status_code=500) from exc
