from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.api.rate_limit import build_rate_limit_dependency
from backend.blog.blog_service import (
    BlogServiceError,
    get_published_blog_post,
    list_published_blog_posts,
    submit_blog_comment,
)
from backend.config.settings import RATE_LIMIT_COMMENT_REQUESTS, RATE_LIMIT_COMMENT_WINDOW_SECONDS
from backend.db.database import get_db


router = APIRouter(prefix="/blog", tags=["blog"])
comment_rate_limit = build_rate_limit_dependency(
    "blog_comment",
    RATE_LIMIT_COMMENT_REQUESTS,
    RATE_LIMIT_COMMENT_WINDOW_SECONDS,
)


class BlogPostSummaryResponse(BaseModel):
    post_id: int
    slug: str
    title: str
    summary: str
    cover_eyebrow: str | None
    author_name: str
    published_at: object
    comment_count: int


class BlogCommentResponse(BaseModel):
    comment_id: int
    post_id: int
    author_name: str
    comment_body: str
    moderation_status: str
    moderation_notes: str | None = None
    created_at: object
    moderated_at: object | None = None


class BlogPostDetailResponse(BaseModel):
    post_id: int
    slug: str
    title: str
    summary: str
    body_text: str
    cover_eyebrow: str | None
    author_name: str
    published_at: object
    comments: list[BlogCommentResponse]


class BlogCommentCreateRequest(BaseModel):
    author_name: str = Field(min_length=2, max_length=80)
    author_email: EmailStr
    comment_body: str = Field(min_length=8, max_length=2000)


def _error_response(exc: BlogServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.get("/posts", response_model=list[BlogPostSummaryResponse])
def list_blog_posts_route(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return list_published_blog_posts(db)


@router.get("/posts/{slug}", response_model=BlogPostDetailResponse)
def get_blog_post_route(slug: str, db: Session = Depends(get_db)) -> Any:
    try:
        return get_published_blog_post(db, slug)
    except BlogServiceError as exc:
        return _error_response(exc)


@router.post("/posts/{post_id}/comments")
def create_blog_comment_route(
    post_id: int,
    payload: BlogCommentCreateRequest,
    request: Request,
    _: None = Depends(comment_rate_limit),
    db: Session = Depends(get_db),
) -> Any:
    client_ip = request.client.host if request.client else None
    try:
        return submit_blog_comment(
            db,
            post_id=post_id,
            author_name=payload.author_name,
            author_email=payload.author_email,
            comment_body=payload.comment_body,
            client_ip=client_ip,
        )
    except BlogServiceError as exc:
        return _error_response(exc)
