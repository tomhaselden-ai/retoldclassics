from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.readers.reader_service import (
    create_reader,
    delete_reader,
    get_reader,
    list_readers,
    update_reader,
)


router = APIRouter(prefix="/readers", tags=["readers"])


class ReaderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0)
    reading_level: str = Field(min_length=1, max_length=50)
    gender_preference: str = Field(min_length=1, max_length=50)
    trait_focus: Any


class ReaderUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0)
    reading_level: str = Field(min_length=1, max_length=50)
    gender_preference: str = Field(min_length=1, max_length=50)
    trait_focus: Any


class ReaderResponse(BaseModel):
    reader_id: int
    account_id: int
    name: str | None
    age: int | None
    reading_level: str | None
    gender_preference: str | None
    trait_focus: Any
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reader_route(
    payload: ReaderCreateRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    reader = create_reader(
        db=db,
        account_id=current_account.account_id,
        name=payload.name,
        age=payload.age,
        reading_level=payload.reading_level,
        gender_preference=payload.gender_preference,
        trait_focus=payload.trait_focus,
    )
    return {
        "reader_id": reader.reader_id,
        "status": "reader_created",
    }


@router.get("", response_model=list[ReaderResponse])
def list_readers_route(
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return list_readers(db, current_account.account_id)


@router.get("/{reader_id}", response_model=ReaderResponse)
def get_reader_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reader(db, current_account.account_id, reader_id)


@router.put("/{reader_id}", response_model=ReaderResponse)
def update_reader_route(
    reader_id: int,
    payload: ReaderUpdateRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return update_reader(
        db=db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        name=payload.name,
        age=payload.age,
        reading_level=payload.reading_level,
        gender_preference=payload.gender_preference,
        trait_focus=payload.trait_focus,
    )


@router.delete("/{reader_id}")
def delete_reader_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    delete_reader(db, current_account.account_id, reader_id)
    return {"status": "reader_deleted"}
