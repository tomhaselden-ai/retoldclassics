from dataclasses import dataclass

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import TIMESTAMP, Column, Integer, MetaData, String, Table, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_PASSWORD_BYTES = 72
metadata = MetaData()

accounts_table = Table(
    "accounts",
    metadata,
    Column("account_id", Integer, primary_key=True),
    Column("email", String(255), nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("subscription_level", String(50)),
    Column("story_security", String(50)),
    Column("allowed_classics_authors", JSON),
    Column("parent_pin_hash", String(255)),
    Column("parent_pin_enabled", Integer),
    Column("failed_pin_attempts", Integer),
    Column("parent_pin_locked_until", TIMESTAMP),
    Column("created_at", TIMESTAMP),
)


@dataclass
class AccountRecord:
    account_id: int
    email: str
    password_hash: str
    subscription_level: str | None
    story_security: str | None
    allowed_classics_authors: object
    parent_pin_hash: str | None
    parent_pin_enabled: int | None
    failed_pin_attempts: int | None
    parent_pin_locked_until: object
    created_at: object


def send_verification_email(email: str) -> None:
    return None


def _to_account_record(row) -> AccountRecord | None:
    if row is None:
        return None
    return AccountRecord(
        account_id=row.account_id,
        email=row.email,
        password_hash=row.password_hash,
        subscription_level=row.subscription_level,
        story_security=row.story_security,
        allowed_classics_authors=getattr(row, "allowed_classics_authors", None),
        parent_pin_hash=getattr(row, "parent_pin_hash", None),
        parent_pin_enabled=getattr(row, "parent_pin_enabled", None),
        failed_pin_attempts=getattr(row, "failed_pin_attempts", None),
        parent_pin_locked_until=getattr(row, "parent_pin_locked_until", None),
        created_at=row.created_at,
    )


def get_account_by_email(db: Session, email: str) -> AccountRecord | None:
    row = db.execute(
        select(accounts_table).where(accounts_table.c.email == email)
    ).mappings().first()
    return _to_account_record(row)


def get_account_by_id(db: Session, account_id: int) -> AccountRecord | None:
    row = db.execute(
        select(accounts_table).where(accounts_table.c.account_id == account_id)
    ).mappings().first()
    return _to_account_record(row)


def hash_password(password: str) -> str:
    _validate_password(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _validate_password(password: str) -> None:
    password_bytes = len(password.encode("utf-8"))
    if password_bytes < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    if password_bytes > MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 bytes or fewer",
        )


def register_account(db: Session, email: str, password: str) -> AccountRecord:
    _validate_password(password)
    existing_account = get_account_by_email(db, email)
    if existing_account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this email already exists",
        )

    insert_stmt = accounts_table.insert().values(
        email=email,
        password_hash=hash_password(password),
        subscription_level="free",
        story_security="private",
        allowed_classics_authors=None,
        parent_pin_hash=None,
        parent_pin_enabled=0,
        failed_pin_attempts=0,
        parent_pin_locked_until=None,
    )

    try:
        result = db.execute(insert_stmt)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this email already exists",
        ) from exc

    account = get_account_by_id(db, int(result.inserted_primary_key[0]))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account",
        )

    send_verification_email(account.email)
    return account


def authenticate_account(db: Session, email: str, password: str) -> AccountRecord:
    account = get_account_by_email(db, email)
    if account is None or not verify_password(password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return account


def update_password(db: Session, account: AccountRecord, new_password: str) -> AccountRecord:
    _validate_password(new_password)
    db.execute(
        accounts_table.update()
        .where(accounts_table.c.account_id == account.account_id)
        .values(password_hash=hash_password(new_password))
    )
    db.commit()

    refreshed = get_account_by_id(db, account.account_id)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )
    return refreshed
