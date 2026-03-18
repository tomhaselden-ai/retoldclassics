from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


metadata = MetaData()

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
)

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
)


@dataclass
class LocationRecord:
    location_id: int
    world_id: int | None
    name: str | None
    description: str | None


def _to_location(row) -> LocationRecord | None:
    if row is None:
        return None
    return LocationRecord(
        location_id=row.location_id,
        world_id=row.world_id,
        name=row.name,
        description=row.description,
    )


def _ensure_world_exists(db: Session, world_id: int) -> None:
    row = db.execute(
        select(worlds_table.c.world_id).where(worlds_table.c.world_id == world_id)
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )


def list_locations(db: Session, world_id: int) -> list[LocationRecord]:
    _ensure_world_exists(db, world_id)

    rows = db.execute(
        select(locations_table)
        .where(locations_table.c.world_id == world_id)
        .order_by(locations_table.c.location_id.asc())
    ).mappings().all()

    return [_to_location(row) for row in rows]


def create_location(db: Session, world_id: int, name: str, description: str | None) -> LocationRecord:
    _ensure_world_exists(db, world_id)

    try:
        result = db.execute(
            locations_table.insert().values(
                world_id=world_id,
                name=name,
                description=description,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create location",
        ) from exc

    location_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(locations_table).where(locations_table.c.location_id == location_id)
    ).mappings().first()

    location = _to_location(row)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created location",
        )
    return location
