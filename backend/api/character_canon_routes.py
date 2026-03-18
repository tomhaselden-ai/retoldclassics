from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.character_canon.enhancement_service import generate_character_canon_preview
from backend.character_canon.service import (
    get_reader_world_character_canon_detail,
    list_reader_world_character_canon_overview,
    publish_reader_world_character_canon,
    save_reader_world_character_canon,
)
from backend.db.database import get_db


router = APIRouter(prefix="/readers", tags=["character-canon"])


class CharacterCanonOverviewItemResponse(BaseModel):
    character_id: int
    name: str | None
    species: str | None
    personality_traits: Any
    home_location: int | None
    canon_status: str
    canon_version: int | None
    is_locked: bool
    is_major_character: bool
    last_reviewed_at: datetime | None
    enhanced_at: datetime | None


class CharacterCanonOverviewResponse(BaseModel):
    reader_id: int
    world_id: int
    reader_world_id: int
    world: dict[str, Any]
    characters: list[CharacterCanonOverviewItemResponse]


class CharacterCanonDetailResponse(BaseModel):
    reader_id: int
    world_id: int
    reader_world_id: int
    world: dict[str, Any]
    character: dict[str, Any]
    canon: dict[str, Any]
    relationships: list[dict[str, Any]]
    world_rules: list[dict[str, Any]]
    recent_memory_events: list[dict[str, Any]]
    history: list[dict[str, Any]]
    enhancement_runs: list[dict[str, Any]]


class CharacterCanonPreviewRequest(BaseModel):
    section_mode: str = Field(default="full", pattern="^(full|narrative|visual)$")


class CharacterCanonPreviewResponse(BaseModel):
    enhancement_run: dict[str, Any]
    preview_profile: dict[str, Any]


class CharacterCanonSaveRequest(BaseModel):
    updates: dict[str, Any] = Field(default_factory=dict)
    enhancement_run_id: int | None = Field(default=None, ge=1)


@router.get(
    "/{reader_id}/worlds/{world_id}/characters/canon",
    response_model=CharacterCanonOverviewResponse,
)
def get_character_canon_overview_route(
    reader_id: int,
    world_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return list_reader_world_character_canon_overview(
        db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=world_id,
    )


@router.get(
    "/{reader_id}/worlds/{world_id}/characters/{character_id}/canon",
    response_model=CharacterCanonDetailResponse,
)
def get_character_canon_detail_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_reader_world_character_canon_detail(
        db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
    )


@router.post(
    "/{reader_id}/worlds/{world_id}/characters/{character_id}/canon/enhance-preview",
    response_model=CharacterCanonPreviewResponse,
)
def enhance_character_canon_preview_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    payload: CharacterCanonPreviewRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return generate_character_canon_preview(
        db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
        section_mode=payload.section_mode,
        existing_canon=None,
    )


@router.put(
    "/{reader_id}/worlds/{world_id}/characters/{character_id}/canon",
    response_model=CharacterCanonDetailResponse,
)
def save_character_canon_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    payload: CharacterCanonSaveRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return save_reader_world_character_canon(
        db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
        updates=payload.updates,
        enhanced_by=current_account.account_id,
        enhancement_run_id=payload.enhancement_run_id,
    )


@router.post(
    "/{reader_id}/worlds/{world_id}/characters/{character_id}/canon/publish",
    response_model=CharacterCanonDetailResponse,
)
def publish_character_canon_route(
    reader_id: int,
    world_id: int,
    character_id: int,
    payload: CharacterCanonSaveRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return publish_reader_world_character_canon(
        db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=world_id,
        character_id=character_id,
        updates=payload.updates,
        enhanced_by=current_account.account_id,
        enhancement_run_id=payload.enhancement_run_id,
    )
