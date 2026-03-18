import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.analytics.analytics_repository import (
    account_exists,
    get_account_reader,
    get_reader_progress,
    list_account_readers,
    list_reader_game_results,
    list_reader_stories,
    list_reader_vocabulary_progress,
)
from backend.analytics.insight_engine import (
    build_account_learning_insights,
    build_reader_learning_insights,
)


logger = logging.getLogger(__name__)


class AnalyticsServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _validate_identifier(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        raise AnalyticsServiceError(error_code="invalid_identifier", status_code=400)
    return value


def _load_reader_insights(db: Session, account_id: int, reader_id: int) -> dict[str, Any]:
    reader = get_account_reader(db, account_id, reader_id)
    if reader is None:
        raise AnalyticsServiceError(error_code="missing_resource", status_code=404)

    progress = get_reader_progress(db, reader.reader_id)
    vocabulary_progress = list_reader_vocabulary_progress(db, reader.reader_id, limit=100)
    game_results = list_reader_game_results(db, reader.reader_id, limit=50)
    stories = list_reader_stories(db, reader.reader_id, limit=10)

    return build_reader_learning_insights(
        reader=reader,
        progress=progress,
        vocabulary_progress=vocabulary_progress,
        game_results=game_results,
        stories=stories,
    )


def get_reader_learning_insights(
    db: Session,
    account_id: int,
    reader_id: Any,
) -> dict[str, Any]:
    normalized_reader_id = _validate_identifier(reader_id)
    logger.info(
        "reader learning insights requested",
        extra={"account_id": account_id, "reader_id": normalized_reader_id},
    )

    try:
        return _load_reader_insights(db, account_id, normalized_reader_id)
    except AnalyticsServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during reader learning insights lookup",
            extra={"account_id": account_id, "reader_id": normalized_reader_id},
        )
        raise AnalyticsServiceError(error_code="database_failure", status_code=500) from exc


def get_account_learning_insights(
    db: Session,
    requesting_account_id: int,
    account_id: Any,
) -> dict[str, Any]:
    normalized_account_id = _validate_identifier(account_id)
    if normalized_account_id != requesting_account_id:
        raise AnalyticsServiceError(error_code="forbidden", status_code=403)

    logger.info(
        "account learning insights requested",
        extra={"account_id": normalized_account_id},
    )

    try:
        if not account_exists(db, normalized_account_id):
            raise AnalyticsServiceError(error_code="missing_resource", status_code=404)

        readers = list_account_readers(db, normalized_account_id)
        reader_insights = [
            _load_reader_insights(db, normalized_account_id, reader.reader_id)
            for reader in readers
        ]
        return build_account_learning_insights(normalized_account_id, reader_insights)
    except AnalyticsServiceError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "database failure during account learning insights lookup",
            extra={"account_id": normalized_account_id},
        )
        raise AnalyticsServiceError(error_code="database_failure", status_code=500) from exc
