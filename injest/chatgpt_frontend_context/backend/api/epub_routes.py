from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.token_manager import get_current_account
from backend.db.database import get_db
from backend.epub.epub_service import EpubService


router = APIRouter(prefix="/stories", tags=["epub"])


class EpubResponse(BaseModel):
    story_id: int
    epub_url: str


class EpubMetadataResponse(BaseModel):
    epub_url: str


@router.post("/{story_id}/export-epub", response_model=EpubResponse, status_code=status.HTTP_201_CREATED)
def export_epub_route(
    story_id: int,
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
