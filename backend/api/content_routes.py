from typing import Any, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.blog.blog_service import BlogServiceError, list_blog_comments_for_moderation, moderate_blog_comment
from backend.content.moderation import require_content_moderator
from backend.contact.contact_service import list_contact_submissions
from backend.db.database import get_db


router = APIRouter(prefix="/parent/content", tags=["content"])


class ModerationCommentResponse(BaseModel):
    comment_id: int
    post_id: int
    post_title: str
    post_slug: str
    author_name: str
    author_email: str
    comment_body: str
    moderation_status: str
    moderation_notes: str | None = None
    created_at: object
    moderated_at: object | None = None


class ContactSubmissionResponse(BaseModel):
    submission_id: int
    name: str
    email: str
    subject: str
    message: str
    delivery_status: str
    created_at: object
    delivered_at: object | None = None


class CommentModerationRequest(BaseModel):
    moderation_status: Literal["approved", "rejected"]
    moderation_notes: str | None = None


def _error_response(exc: BlogServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/comments", response_model=list[ModerationCommentResponse])
def list_blog_comments_for_moderation_route(
    moderation_status: str | None = None,
    current_account=Depends(require_content_moderator),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return list_blog_comments_for_moderation(db, moderation_status=moderation_status)


@router.patch("/comments/{comment_id}")
def moderate_blog_comment_route(
    comment_id: int,
    payload: CommentModerationRequest,
    current_account=Depends(require_content_moderator),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return moderate_blog_comment(
            db,
            comment_id=comment_id,
            moderation_status=payload.moderation_status,
            moderation_notes=payload.moderation_notes,
            moderated_by_email=current_account.email,
        )
    except BlogServiceError as exc:
        return _error_response(exc)


@router.get("/contact-submissions", response_model=list[ContactSubmissionResponse])
def list_contact_submissions_route(
    delivery_status: str | None = None,
    current_account=Depends(require_content_moderator),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return list_contact_submissions(db, delivery_status=delivery_status)
