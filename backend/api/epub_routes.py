from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.rate_limit import build_rate_limit_dependency
from backend.auth.token_manager import get_current_account
from backend.config.settings import RATE_LIMIT_PUBLISH_REQUESTS, RATE_LIMIT_PUBLISH_WINDOW_SECONDS
from backend.db.database import get_db
from backend.epub.epub_service import EpubService


router = APIRouter(prefix="/stories", tags=["epub"])
publish_rate_limit = build_rate_limit_dependency(
    "story_export_epub",
    RATE_LIMIT_PUBLISH_REQUESTS,
    RATE_LIMIT_PUBLISH_WINDOW_SECONDS,
    key_scope="account",
    account_dependency=get_current_account,
)


class EpubResponse(BaseModel):
    story_id: int
    epub_url: str


class EpubMetadataResponse(BaseModel):
    epub_url: str


@router.post("/{story_id}/export-epub", response_model=EpubResponse, status_code=status.HTTP_201_CREATED)
def export_epub_route(
    story_id: int,
    request: Request,
    _: None = Depends(publish_rate_limit),
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = EpubService()
    return service.export_story_epub(db, current_account.account_id, story_id)


@router.get("/{story_id}/epub", response_model=EpubMetadataResponse)
def get_epub_route(
    story_id: int,
    current_account=Depends(get_current_account),
    db: Session = Depends(get_db),
):
    service = EpubService()
    return service.get_story_epub(db, current_account.account_id, story_id)
