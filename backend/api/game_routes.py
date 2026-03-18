from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.games.game_service import GameServiceError, get_game_history
from backend.games.game_reporting_service import (
    GameReportingServiceError,
    get_reader_game_practice_summary,
)
from backend.games.game_session_service import (
    GameSessionServiceError,
    complete_v1_game_session,
    create_v1_game_session,
    get_game_catalog,
    get_v1_game_session,
)


router = APIRouter(prefix="/readers", tags=["games"])


class GameGenerateRequest(BaseModel):
    game_type: str
    story_id: int | None = Field(default=None, ge=1)
    difficulty_level: int | None = Field(default=None, ge=1, le=3)
    question_count: int | None = Field(default=None, ge=1, le=10)


class GameQuestionResponse(BaseModel):
    question_id: str
    prompt: str
    context_text: str | None
    choices: list[str]
    answer: str


class GameGenerateResponse(BaseModel):
    reader_id: int
    game_type: str
    story_id: int | None
    difficulty_level: int
    questions: list[GameQuestionResponse]


class GameResultCreateRequest(BaseModel):
    game_type: str
    difficulty_level: int = Field(ge=1, le=3)
    score: int = Field(ge=0, le=100)
    duration_seconds: int = Field(ge=1)


class GameResultCreateResponse(BaseModel):
    game_result_id: int
    status: str


class GameHistoryItemResponse(BaseModel):
    game_result_id: int
    game_type: str | None
    difficulty_level: int | None
    score: int | None
    duration_seconds: int | None
    played_at: datetime | None


class GameCatalogItemResponse(BaseModel):
    game_type: str
    label: str
    description: str
    default_item_count: int
    supports_story_source: bool


class GameCatalogRecentSessionResponse(BaseModel):
    session_id: int
    game_type: str
    completion_status: str
    duration_seconds: int | None
    started_at: datetime | None
    ended_at: datetime | None


class GameCatalogResponse(BaseModel):
    reader_id: int
    recommended_difficulty: int
    games: list[GameCatalogItemResponse]
    recent_sessions: list[GameCatalogRecentSessionResponse]


class GameSessionWordItemResponse(BaseModel):
    word_id: int | None
    word: str
    definition: str | None
    example_sentence: str | None
    difficulty_level: int | None
    reader_id: int
    story_id: int | None
    source_type: str
    trait_focus: str | None


class GameSessionStartRequest(BaseModel):
    game_type: str
    story_id: int | None = Field(default=None, ge=1)
    source_type: str | None = None
    difficulty_level: int | None = Field(default=None, ge=1, le=3)
    item_count: int | None = Field(default=None, ge=4, le=16)


class GameSessionResponse(BaseModel):
    session_id: int
    reader_id: int
    game_type: str
    source_type: str
    source_story_id: int | None
    difficulty_level: int
    status: str
    completion_status: str
    started_at: datetime | None
    items: list[GameSessionWordItemResponse]
    payload: dict[str, Any]


class GameWordAttemptPayload(BaseModel):
    word_id: int | None = Field(default=None, ge=1)
    word_text: str
    attempt_count: int = Field(ge=0)
    correct: bool
    time_spent_seconds: int = Field(ge=0)
    hint_used: bool = False
    skipped: bool = False


class GameSessionCompleteRequest(BaseModel):
    completion_status: str
    duration_seconds: int = Field(ge=1)
    attempts: list[GameWordAttemptPayload]


class GameSessionCompleteResponse(BaseModel):
    session_id: int
    reader_id: int
    game_type: str
    difficulty_level: int
    status: str
    completion_status: str
    words_attempted: int
    words_correct: int
    words_incorrect: int
    hints_used: int
    duration_seconds: int | None
    legacy_game_result_id: int


class GameWordAttemptResponse(BaseModel):
    attempt_id: int
    word_id: int | None
    word_text: str
    game_type: str
    attempt_count: int
    correct: bool
    time_spent_seconds: int
    hint_used: bool
    skipped: bool
    created_at: datetime | None


class GameSessionDetailResponse(BaseModel):
    session_id: int
    reader_id: int
    game_type: str
    source_type: str
    source_story_id: int | None
    difficulty_level: int
    status: str
    item_count: int
    words_attempted: int
    words_correct: int
    words_incorrect: int
    hints_used: int
    completion_status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    items: list[GameSessionWordItemResponse]
    payload: dict[str, Any] | None
    attempts: list[GameWordAttemptResponse]


class GameAccuracyByTypeResponse(BaseModel):
    game_type: str
    sessions_played: int
    words_attempted: int
    words_correct: int
    success_rate: float | None


class RepeatedMissedWordResponse(BaseModel):
    word_text: str
    miss_count: int


class GamePracticeSummaryResponse(BaseModel):
    sessions_total: int
    sessions_this_week: int
    words_practiced: int
    words_correct: int
    average_success_rate: float | None
    practice_time_seconds: int
    strongest_game_type: str | None
    weakest_game_type: str | None
    improvement_trend: str
    accuracy_by_game_type: list[GameAccuracyByTypeResponse]
    repeated_missed_words: list[RepeatedMissedWordResponse]


def _error_response(exc: GameServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code},
    )


def _session_error_response(exc: GameSessionServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code},
    )


def _reporting_error_response(exc: GameReportingServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code},
    )


@router.post("/{reader_id}/games/generate", response_model=GameGenerateResponse)
def generate_game_route(
    reader_id: int,
    payload: GameGenerateRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    return JSONResponse(
        status_code=410,
        content={"error": "game_system_replaced", "message": "Use the V1 session-based game endpoints instead."},
    )


@router.get("/{reader_id}/games/catalog", response_model=GameCatalogResponse)
def get_game_catalog_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_game_catalog(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
        )
    except GameSessionServiceError as exc:
        return _session_error_response(exc)


@router.post("/{reader_id}/games/sessions", response_model=GameSessionResponse)
def create_game_session_route(
    reader_id: int,
    payload: GameSessionStartRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return create_v1_game_session(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            game_type=payload.game_type,
            story_id=payload.story_id,
            source_type=payload.source_type,
            difficulty_level=payload.difficulty_level,
            item_count=payload.item_count,
        )
    except GameSessionServiceError as exc:
        return _session_error_response(exc)


@router.get("/{reader_id}/games/sessions/{session_id}", response_model=GameSessionDetailResponse)
def get_game_session_route(
    reader_id: int,
    session_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_v1_game_session(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            session_id=session_id,
        )
    except GameSessionServiceError as exc:
        return _session_error_response(exc)


@router.get("/{reader_id}/games/summary", response_model=GamePracticeSummaryResponse)
def get_game_summary_route(
    reader_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return get_reader_game_practice_summary(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
        )
    except GameReportingServiceError as exc:
        return _reporting_error_response(exc)


@router.post("/{reader_id}/games/sessions/{session_id}/complete", response_model=GameSessionCompleteResponse)
def complete_game_session_route(
    reader_id: int,
    session_id: int,
    payload: GameSessionCompleteRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    try:
        return complete_v1_game_session(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            session_id=session_id,
            completion_status=payload.completion_status,
            duration_seconds=payload.duration_seconds,
            attempts=[attempt.model_dump() for attempt in payload.attempts],
        )
    except GameSessionServiceError as exc:
        return _session_error_response(exc)


@router.post("/{reader_id}/games/results", response_model=GameResultCreateResponse)
def record_game_result_route(
    reader_id: int,
    payload: GameResultCreateRequest,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    return JSONResponse(
        status_code=410,
        content={"error": "game_system_replaced", "message": "Save V1 game sessions through the session completion endpoint."},
    )


@router.get("/{reader_id}/games/history", response_model=list[GameHistoryItemResponse])
def get_game_history_route(
    reader_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return get_game_history(
            db=db,
            account_id=current_account.account_id,
            reader_id=reader_id,
            limit=limit,
        )
    except GameServiceError as exc:
        return _error_response(exc)
