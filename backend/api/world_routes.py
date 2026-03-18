from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.worlds.character_service import create_character, list_characters
from backend.worlds.location_service import create_location, list_locations
from backend.worlds.relationship_graph import create_relationship, list_relationships
from backend.worlds.world_service import (
    assign_world_to_reader,
    create_reader_world_character,
    create_reader_world_location,
    create_reader_world_relationship,
    get_reader_world_details,
    get_world_details,
    list_reader_worlds,
    list_worlds,
)


router = APIRouter(tags=["worlds"])


class WorldResponse(BaseModel):
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None

    model_config = ConfigDict(from_attributes=True)


class WorldRuleResponse(BaseModel):
    rule_id: int
    world_id: int
    rule_type: str | None
    rule_description: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LocationResponse(BaseModel):
    location_id: int
    world_id: int | None
    name: str | None
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class CharacterResponse(BaseModel):
    character_id: int
    world_id: int | None
    name: str | None
    species: str | None
    personality_traits: Any
    home_location: int | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AssignWorldRequest(BaseModel):
    world_id: int | None = Field(default=None, ge=1)
    custom_name: str | None = Field(default=None, max_length=255)


class ReaderWorldResponse(BaseModel):
    reader_world_id: int
    reader_id: int | None
    world_id: int | None
    custom_name: str | None
    created_at: datetime | None
    world: WorldResponse

    model_config = ConfigDict(from_attributes=True)


class CreateCharacterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    species: str = Field(min_length=1, max_length=100)
    personality_traits: Any
    home_location: int | None = None


class CreateLocationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class RelationshipResponse(BaseModel):
    relationship_id: int
    character_a: int | None
    character_b: int | None
    relationship_type: str | None
    relationship_strength: int | None
    last_interaction: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WorldDetailsResponse(BaseModel):
    world: WorldResponse
    locations: list[LocationResponse]
    characters: list[CharacterResponse]
    relationships: list[RelationshipResponse] = []
    world_rules: list[WorldRuleResponse]


class CreateRelationshipRequest(BaseModel):
    character_a: int
    character_b: int
    relationship_type: str = Field(min_length=1, max_length=100)
    relationship_strength: int = Field(ge=0)


@router.get("/worlds", response_model=list[WorldResponse])
def list_worlds_route(db: Session = Depends(get_db)):
    return list_worlds(db)


@router.get("/worlds/{world_id}", response_model=WorldDetailsResponse)
def get_world_details_route(
    world_id: int,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_world_details(db, world_id)


@router.get("/readers/{reader_id}/worlds/{world_id}/details", response_model=WorldDetailsResponse)
def get_reader_world_details_route(
    reader_id: int,
    world_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return get_reader_world_details(db, current_account.account_id, reader_id, world_id)


@router.post("/readers/{reader_id}/worlds", status_code=status.HTTP_201_CREATED)
def assign_world_to_reader_route(
    reader_id: int,
    payload: AssignWorldRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    reader_world = assign_world_to_reader(
        db=db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        world_id=payload.world_id,
        custom_name=payload.custom_name,
    )
    return {
        "reader_world_id": reader_world.reader_world_id,
        "status": "world_assigned",
    }


@router.get("/readers/{reader_id}/worlds", response_model=list[ReaderWorldResponse])
def list_reader_worlds_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return list_reader_worlds(db, current_account.account_id, reader_id)


@router.get("/worlds/{world_id}/characters", response_model=list[CharacterResponse])
def list_characters_route(
    world_id: int,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return list_characters(db, world_id)


@router.post("/worlds/{world_id}/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character_route(
    world_id: int,
    payload: CreateCharacterRequest,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_character(
        db=db,
        world_id=world_id,
        name=payload.name,
        species=payload.species,
        personality_traits=payload.personality_traits,
        home_location=payload.home_location,
    )


@router.get("/worlds/{world_id}/locations", response_model=list[LocationResponse])
def list_locations_route(
    world_id: int,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return list_locations(db, world_id)


@router.post("/worlds/{world_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location_route(
    world_id: int,
    payload: CreateLocationRequest,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_location(
        db=db,
        world_id=world_id,
        name=payload.name,
        description=payload.description,
    )


@router.get("/worlds/{world_id}/relationships", response_model=list[RelationshipResponse])
def list_relationships_route(
    world_id: int,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return list_relationships(db, world_id)


@router.post("/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
def create_relationship_route(
    payload: CreateRelationshipRequest,
    _: Any = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_relationship(
        db=db,
        character_a=payload.character_a,
        character_b=payload.character_b,
        relationship_type=payload.relationship_type,
        relationship_strength=payload.relationship_strength,
    )


@router.post(
    "/readers/{reader_id}/worlds/{world_id}/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reader_world_location_route(
    reader_id: int,
    world_id: int,
    payload: CreateLocationRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_reader_world_location(
        db=db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        template_world_id=world_id,
        name=payload.name,
        description=payload.description,
    )


@router.post(
    "/readers/{reader_id}/worlds/{world_id}/characters",
    response_model=CharacterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reader_world_character_route(
    reader_id: int,
    world_id: int,
    payload: CreateCharacterRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_reader_world_character(
        db=db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        template_world_id=world_id,
        name=payload.name,
        species=payload.species,
        personality_traits=payload.personality_traits,
        home_location=payload.home_location,
    )


@router.post(
    "/readers/{reader_id}/worlds/{world_id}/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reader_world_relationship_route(
    reader_id: int,
    world_id: int,
    payload: CreateRelationshipRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return create_reader_world_relationship(
        db=db,
        account_id=current_account.account_id,
        reader_id=reader_id,
        template_world_id=world_id,
        character_a=payload.character_a,
        character_b=payload.character_b,
        relationship_type=payload.relationship_type,
        relationship_strength=payload.relationship_strength,
    )
