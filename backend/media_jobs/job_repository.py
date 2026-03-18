from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, and_, asc, desc, func, select, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

media_jobs_table = Table(
    "media_jobs",
    metadata,
    Column("job_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("story_id", Integer, nullable=False),
    Column("job_type", String(50), nullable=False),
    Column("status", String(20), nullable=False),
    Column("error_message", Text),
    Column("result_payload", JSON),
    Column("worker_id", String(100)),
    Column("attempt_count", Integer, nullable=False),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
    Column("started_at", TIMESTAMP),
    Column("completed_at", TIMESTAMP),
)


ACTIVE_JOB_STATUSES = {"pending", "processing"}
TERMINAL_JOB_STATUSES = {"completed", "failed"}


@dataclass
class MediaJobRecord:
    job_id: int
    account_id: int
    story_id: int
    job_type: str
    status: str
    error_message: str | None
    result_payload: Any
    worker_id: str | None
    attempt_count: int
    created_at: datetime | None
    updated_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


def _to_media_job(row) -> MediaJobRecord | None:
    if row is None:
        return None
    return MediaJobRecord(
        job_id=row.job_id,
        account_id=row.account_id,
        story_id=row.story_id,
        job_type=row.job_type,
        status=row.status,
        error_message=row.error_message,
        result_payload=row.result_payload,
        worker_id=row.worker_id,
        attempt_count=row.attempt_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


def create_media_job(db: Session, account_id: int, story_id: int, job_type: str) -> MediaJobRecord:
    result = db.execute(
        media_jobs_table.insert().values(
            account_id=account_id,
            story_id=story_id,
            job_type=job_type,
            status="pending",
            error_message=None,
            result_payload=None,
            worker_id=None,
            attempt_count=0,
        )
    )
    job_id = int(result.inserted_primary_key[0])
    row = db.execute(select(media_jobs_table).where(media_jobs_table.c.job_id == job_id)).mappings().first()
    job = _to_media_job(row)
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Media job could not be created")
    return job


def create_completed_media_job(
    db: Session,
    account_id: int,
    story_id: int,
    job_type: str,
    result_payload: dict[str, Any],
) -> MediaJobRecord:
    result = db.execute(
        media_jobs_table.insert().values(
            account_id=account_id,
            story_id=story_id,
            job_type=job_type,
            status="completed",
            error_message=None,
            result_payload=result_payload,
            worker_id="inline-status",
            attempt_count=0,
            started_at=func.now(),
            completed_at=func.now(),
        )
    )
    job_id = int(result.inserted_primary_key[0])
    row = db.execute(select(media_jobs_table).where(media_jobs_table.c.job_id == job_id)).mappings().first()
    job = _to_media_job(row)
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Media job could not be created")
    return job


def get_media_job(db: Session, job_id: int) -> MediaJobRecord:
    row = db.execute(select(media_jobs_table).where(media_jobs_table.c.job_id == job_id)).mappings().first()
    job = _to_media_job(row)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media job not found")
    return job


def get_media_job_for_account(db: Session, job_id: int, account_id: int) -> MediaJobRecord:
    row = db.execute(
        select(media_jobs_table).where(
            and_(
                media_jobs_table.c.job_id == job_id,
                media_jobs_table.c.account_id == account_id,
            )
        )
    ).mappings().first()
    job = _to_media_job(row)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media job not found")
    return job


def get_latest_story_media_job(
    db: Session,
    account_id: int,
    story_id: int,
    job_type: str,
) -> MediaJobRecord | None:
    row = db.execute(
        select(media_jobs_table)
        .where(
            and_(
                media_jobs_table.c.account_id == account_id,
                media_jobs_table.c.story_id == story_id,
                media_jobs_table.c.job_type == job_type,
            )
        )
        .order_by(desc(media_jobs_table.c.created_at), desc(media_jobs_table.c.job_id))
    ).mappings().first()
    return _to_media_job(row)


def get_active_story_media_job(
    db: Session,
    account_id: int,
    story_id: int,
    job_type: str,
) -> MediaJobRecord | None:
    row = db.execute(
        select(media_jobs_table)
        .where(
            and_(
                media_jobs_table.c.account_id == account_id,
                media_jobs_table.c.story_id == story_id,
                media_jobs_table.c.job_type == job_type,
                media_jobs_table.c.status.in_(ACTIVE_JOB_STATUSES),
            )
        )
        .order_by(asc(media_jobs_table.c.created_at), asc(media_jobs_table.c.job_id))
    ).mappings().first()
    return _to_media_job(row)


def claim_next_media_job(db: Session, worker_id: str) -> MediaJobRecord | None:
    row = db.execute(
        select(media_jobs_table)
        .where(media_jobs_table.c.status == "pending")
        .order_by(asc(media_jobs_table.c.created_at), asc(media_jobs_table.c.job_id))
    ).mappings().first()
    if row is None:
        return None

    claimed = db.execute(
        media_jobs_table.update()
        .where(
            and_(
                media_jobs_table.c.job_id == row["job_id"],
                media_jobs_table.c.status == "pending",
            )
        )
        .values(
            status="processing",
            worker_id=worker_id,
            started_at=func.now(),
            attempt_count=media_jobs_table.c.attempt_count + 1,
            error_message=None,
        )
    )
    if claimed.rowcount != 1:
        db.rollback()
        return None

    db.commit()
    claimed_row = db.execute(select(media_jobs_table).where(media_jobs_table.c.job_id == row["job_id"])).mappings().first()
    return _to_media_job(claimed_row)


def complete_media_job(db: Session, job_id: int, result_payload: dict[str, Any]) -> MediaJobRecord:
    db.execute(
        media_jobs_table.update()
        .where(media_jobs_table.c.job_id == job_id)
        .values(
            status="completed",
            result_payload=result_payload,
            error_message=None,
            completed_at=func.now(),
        )
    )
    db.commit()
    return get_media_job(db, job_id)


def fail_media_job(db: Session, job_id: int, error_message: str) -> MediaJobRecord:
    db.execute(
        media_jobs_table.update()
        .where(media_jobs_table.c.job_id == job_id)
        .values(
            status="failed",
            error_message=error_message,
            completed_at=func.now(),
        )
    )
    db.commit()
    return get_media_job(db, job_id)
