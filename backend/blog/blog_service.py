from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class BlogServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _serialize_comment(row: Any) -> dict[str, Any]:
    return {
        "comment_id": row["comment_id"],
        "post_id": row["post_id"],
        "author_name": row["author_name"],
        "comment_body": row["comment_body"],
        "moderation_status": row["moderation_status"],
        "moderation_notes": row.get("moderation_notes"),
        "created_at": row["created_at"],
        "moderated_at": row.get("moderated_at"),
    }


def _serialize_post_summary(row: Any) -> dict[str, Any]:
    return {
        "post_id": row["post_id"],
        "slug": row["slug"],
        "title": row["title"],
        "summary": row["summary"],
        "cover_eyebrow": row["cover_eyebrow"],
        "author_name": row["author_name"],
        "published_at": row["published_at"],
        "comment_count": row["comment_count"],
    }


def list_published_blog_posts(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                post_id,
                slug,
                title,
                summary,
                cover_eyebrow,
                author_name,
                published_at,
                (
                    SELECT COUNT(*)
                    FROM blog_comments
                    WHERE blog_comments.post_id = blog_posts.post_id
                      AND moderation_status = 'approved'
                ) AS comment_count
            FROM blog_posts
            WHERE status = 'published'
            ORDER BY published_at DESC, post_id DESC
            """
        )
    ).mappings().all()
    return [_serialize_post_summary(row) for row in rows]


def get_published_blog_post(db: Session, slug: str) -> dict[str, Any]:
    post = db.execute(
        text(
            """
            SELECT post_id, slug, title, summary, body_text, cover_eyebrow, author_name, published_at
            FROM blog_posts
            WHERE slug = :slug
              AND status = 'published'
            LIMIT 1
            """
        ),
        {"slug": slug},
    ).mappings().first()

    if post is None:
        raise BlogServiceError(error_code="blog_post_not_found", status_code=404)

    comments = db.execute(
        text(
            """
            SELECT
                comment_id,
                post_id,
                author_name,
                comment_body,
                moderation_status,
                moderation_notes,
                created_at,
                moderated_at
            FROM blog_comments
            WHERE post_id = :post_id
              AND moderation_status = 'approved'
            ORDER BY created_at ASC
            """
        ),
        {"post_id": post["post_id"]},
    ).mappings().all()

    return {
        "post_id": post["post_id"],
        "slug": post["slug"],
        "title": post["title"],
        "summary": post["summary"],
        "body_text": post["body_text"],
        "cover_eyebrow": post["cover_eyebrow"],
        "author_name": post["author_name"],
        "published_at": post["published_at"],
        "comments": [_serialize_comment(row) for row in comments],
    }


def submit_blog_comment(
    db: Session,
    post_id: int,
    author_name: str,
    author_email: str,
    comment_body: str,
    client_ip: str | None,
) -> dict[str, Any]:
    post = db.execute(
        text("SELECT post_id FROM blog_posts WHERE post_id = :post_id AND status = 'published' LIMIT 1"),
        {"post_id": post_id},
    ).mappings().first()
    if post is None:
        raise BlogServiceError(error_code="blog_post_not_found", status_code=404)

    result = db.execute(
        text(
            """
            INSERT INTO blog_comments (
                post_id,
                author_name,
                author_email,
                comment_body,
                moderation_status,
                client_ip
            ) VALUES (
                :post_id,
                :author_name,
                :author_email,
                :comment_body,
                'pending',
                :client_ip
            )
            """
        ),
        {
            "post_id": post_id,
            "author_name": author_name.strip(),
            "author_email": author_email.strip().lower(),
            "comment_body": comment_body.strip(),
            "client_ip": client_ip,
        },
    )
    db.commit()

    return {
        "status": "pending_moderation",
        "comment_id": result.lastrowid,
    }


def list_blog_comments_for_moderation(
    db: Session,
    moderation_status: str | None = None,
) -> list[dict[str, Any]]:
    where_clause = ""
    params: dict[str, Any] = {}
    if moderation_status:
        where_clause = "WHERE c.moderation_status = :moderation_status"
        params["moderation_status"] = moderation_status

    rows = db.execute(
        text(
            f"""
            SELECT
                c.comment_id,
                c.post_id,
                p.title AS post_title,
                p.slug AS post_slug,
                c.author_name,
                c.author_email,
                c.comment_body,
                c.moderation_status,
                c.moderation_notes,
                c.created_at,
                c.moderated_at
            FROM blog_comments c
            JOIN blog_posts p ON p.post_id = c.post_id
            {where_clause}
            ORDER BY
                CASE c.moderation_status
                    WHEN 'pending' THEN 0
                    WHEN 'approved' THEN 1
                    ELSE 2
                END,
                c.created_at DESC
            """
        ),
        params,
    ).mappings().all()

    return [
        {
            "comment_id": row["comment_id"],
            "post_id": row["post_id"],
            "post_title": row["post_title"],
            "post_slug": row["post_slug"],
            "author_name": row["author_name"],
            "author_email": row["author_email"],
            "comment_body": row["comment_body"],
            "moderation_status": row["moderation_status"],
            "moderation_notes": row["moderation_notes"],
            "created_at": row["created_at"],
            "moderated_at": row["moderated_at"],
        }
        for row in rows
    ]


def moderate_blog_comment(
    db: Session,
    comment_id: int,
    moderation_status: str,
    moderation_notes: str | None,
    moderated_by_email: str,
) -> dict[str, Any]:
    existing = db.execute(
        text("SELECT comment_id FROM blog_comments WHERE comment_id = :comment_id LIMIT 1"),
        {"comment_id": comment_id},
    ).mappings().first()
    if existing is None:
        raise BlogServiceError(error_code="blog_comment_not_found", status_code=404)

    db.execute(
        text(
            """
            UPDATE blog_comments
            SET moderation_status = :moderation_status,
                moderation_notes = :moderation_notes,
                moderated_at = CURRENT_TIMESTAMP,
                moderated_by_email = :moderated_by_email
            WHERE comment_id = :comment_id
            """
        ),
        {
            "comment_id": comment_id,
            "moderation_status": moderation_status,
            "moderation_notes": moderation_notes.strip() if moderation_notes else None,
            "moderated_by_email": moderated_by_email.strip().lower(),
        },
    )
    db.commit()

    return {"status": moderation_status, "comment_id": comment_id}
