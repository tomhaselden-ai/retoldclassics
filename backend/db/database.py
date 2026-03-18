import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import DATABASE_URL, is_production_env


DEFAULT_DATABASE_URL = (
    "mysql+pymysql://user:password@localhost/persistent_story_universe"
)

logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    if DATABASE_URL:
        return DATABASE_URL
    if is_production_env():
        raise RuntimeError("DATABASE_URL must be configured when APP_ENV is production")
    logger.warning("DATABASE_URL is not configured; using development fallback database URL")
    return DEFAULT_DATABASE_URL

engine = create_engine(
    _resolve_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
