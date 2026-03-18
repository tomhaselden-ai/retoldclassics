import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SOURCE_DATABASE_URL = os.getenv(
    "SOURCE_DATABASE_URL",
    "mysql+pymysql://user:password@localhost/stories",
)

DESTINATION_DATABASE_URL = os.getenv(
    "DESTINATION_DATABASE_URL",
    "mysql+pymysql://user:password@localhost/persistent_story_universe",
)


source_engine = create_engine(
    SOURCE_DATABASE_URL,
    pool_pre_ping=True,
)

destination_engine = create_engine(
    DESTINATION_DATABASE_URL,
    pool_pre_ping=True,
)


SourceSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=source_engine,
)

DestinationSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=destination_engine,
)
