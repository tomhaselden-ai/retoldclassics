from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.goals.goal_service import (
    GoalServiceError,
    create_reader_goal,
    list_parent_goals_with_progress,
    list_reader_goals_with_progress,
    update_reader_goal,
)


router = APIRouter(tags=["goals"])


class GoalProgressResponse(BaseModel):
    current_value: int
    target_value: int
    progress_percent: int
    status: str
    updated_at: datetime | None
    completed_at: datetime | None


class GoalResponse(BaseModel):
    goal_id: int
    reader_id: int
    goal_type: str
    title: str
    target_value: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    progress: GoalProgressResponse


class ParentGoalReaderResponse(BaseModel):
    reader_id: int
    name: str | None
    reading_level: str | None
    proficiency: str
    goals: list[GoalResponse]


class ParentGoalsResponse(BaseModel):
    account_id: int
    active_goal_count: int
    completed_goal_count: int
    readers: list[ParentGoalReaderResponse]


class ReaderGoalsResponse(BaseModel):
    reader: dict[str, Any]
    goals: list[GoalResponse]


class CreateGoalRequest(BaseModel):
    goal_type: str
    target_value: int = Field(ge=1)
    title: str | None = Field(default=None, max_length=255)


class UpdateGoalRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    target_value: int = Field(ge=1)
    is_active: bool


def _error_response(exc: GoalServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/parent/goals", response_model=ParentGoalsResponse)
def get_parent_goals_route(
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return list_parent_goals_with_progress(db, current_account.account_id)
    except GoalServiceError as exc:
        return _error_response(exc)


@router.post("/parent/readers/{reader_id}/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_reader_goal_route(
    reader_id: int,
    payload: CreateGoalRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return create_reader_goal(
            db,
            current_account.account_id,
            reader_id,
            payload.goal_type,
            payload.target_value,
            payload.title,
        )
    except GoalServiceError as exc:
        return _error_response(exc)


@router.patch("/parent/goals/{goal_id}", response_model=GoalResponse)
def update_goal_route(
    goal_id: int,
    payload: UpdateGoalRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return update_reader_goal(
            db,
            current_account.account_id,
            goal_id,
            title=payload.title,
            target_value=payload.target_value,
            is_active=payload.is_active,
        )
    except GoalServiceError as exc:
        return _error_response(exc)


@router.get("/readers/{reader_id}/goals", response_model=ReaderGoalsResponse)
def get_reader_goals_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return list_reader_goals_with_progress(db, current_account.account_id, reader_id)
    except GoalServiceError as exc:
        return _error_response(exc)
