from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.auth_service import AccountRecord, accounts_table, get_account_by_id
from backend.classics.classics_serializer import ALLOWED_AUTHORS


def get_account_profile(db: Session, account_id: int) -> AccountRecord:
    account = get_account_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


def update_account_profile(
    db: Session,
    account_id: int,
    subscription_level: str,
    story_security: str,
    allowed_classics_authors: list[str] | None,
) -> AccountRecord:
    if not subscription_level.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription_level",
        )

    if not story_security.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid story_security",
        )

    normalized_authors = None
    if allowed_classics_authors is not None:
        invalid_authors = [author for author in allowed_classics_authors if author not in ALLOWED_AUTHORS]
        if invalid_authors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid allowed_classics_authors",
            )
        normalized_authors = list(dict.fromkeys(allowed_classics_authors))

    db.execute(
        accounts_table.update()
        .where(accounts_table.c.account_id == account_id)
        .values(
            subscription_level=subscription_level,
            story_security=story_security,
            allowed_classics_authors=normalized_authors,
        )
    )
    db.commit()

    account = get_account_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account
