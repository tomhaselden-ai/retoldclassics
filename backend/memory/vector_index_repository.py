from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, and_, select
from sqlalchemy.orm import Session


metadata = MetaData()

vector_memory_index_table = Table(
    "vector_memory_index",
    metadata,
    Column("vector_id", String(128), primary_key=True),
    Column("source_type", String(50)),
    Column("source_id", Integer),
    Column("created_at", TIMESTAMP),
)


@dataclass
class VectorIndexRecord:
    vector_id: str
    source_type: str | None
    source_id: int | None
    created_at: datetime | None


def _to_vector_index(row) -> VectorIndexRecord | None:
    if row is None:
        return None
    return VectorIndexRecord(
        vector_id=row.vector_id,
        source_type=row.source_type,
        source_id=row.source_id,
        created_at=row.created_at,
    )


def get_vector_index_by_source(
    db: Session,
    source_type: str,
    source_id: int,
) -> VectorIndexRecord | None:
    row = db.execute(
        select(vector_memory_index_table).where(
            and_(
                vector_memory_index_table.c.source_type == source_type,
                vector_memory_index_table.c.source_id == source_id,
            )
        )
    ).mappings().first()
    return _to_vector_index(row)


def insert_vector_index(
    db: Session,
    vector_id: str,
    source_type: str,
    source_id: int,
) -> VectorIndexRecord:
    db.execute(
        vector_memory_index_table.insert().values(
            vector_id=vector_id,
            source_type=source_type,
            source_id=source_id,
        )
    )
    row = db.execute(
        select(vector_memory_index_table).where(vector_memory_index_table.c.vector_id == vector_id)
    ).mappings().first()
    record = _to_vector_index(row)
    if record is None:
        raise RuntimeError("Inserted vector index could not be reloaded")
    return record
