import logging
import smtplib
from email.message import EmailMessage
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config.settings import (
    CONTACT_DESTINATION_EMAIL,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
    is_production_env,
)


logger = logging.getLogger(__name__)


class ContactServiceError(Exception):
    def __init__(self, error_code: str, status_code: int) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.status_code = status_code


def _send_contact_notification_email(name: str, email: str, subject: str, message: str) -> bool:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        if is_production_env():
            raise ContactServiceError(error_code="contact_email_not_configured", status_code=500)
        logger.warning("SMTP is not configured; contact submission from %s was stored only", email)
        return False

    outgoing = EmailMessage()
    outgoing["From"] = SMTP_FROM_EMAIL
    outgoing["To"] = CONTACT_DESTINATION_EMAIL
    outgoing["Reply-To"] = email
    outgoing["Subject"] = f"StoryBloom contact: {subject}"
    outgoing.set_content(
        "\n".join(
            [
                f"Name: {name}",
                f"Email: {email}",
                "",
                message,
            ]
        )
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(outgoing)
    except Exception as exc:  # pragma: no cover - exercised through runtime behavior
        logger.exception("Failed to deliver contact submission email from %s", email)
        raise ContactServiceError(error_code="contact_delivery_failed", status_code=500) from exc

    return True


def create_contact_submission(
    db: Session,
    name: str,
    email: str,
    subject: str,
    message: str,
    client_ip: str | None,
) -> dict[str, Any]:
    result = db.execute(
        text(
            """
            INSERT INTO contact_submissions (
                name,
                email,
                subject,
                message,
                delivery_status,
                client_ip
            ) VALUES (
                :name,
                :email,
                :subject,
                :message,
                'queued',
                :client_ip
            )
            """
        ),
        {
            "name": name.strip(),
            "email": email.strip().lower(),
            "subject": subject.strip(),
            "message": message.strip(),
            "client_ip": client_ip,
        },
    )
    submission_id = result.lastrowid
    db.commit()

    delivered = False
    try:
        delivered = _send_contact_notification_email(name=name, email=email, subject=subject, message=message)
    finally:
        db.execute(
            text(
                """
                UPDATE contact_submissions
                SET delivery_status = :delivery_status,
                    delivered_at = CASE
                        WHEN :delivery_status = 'delivered' THEN CURRENT_TIMESTAMP
                        ELSE delivered_at
                    END
                WHERE submission_id = :submission_id
                """
            ),
            {
                "submission_id": submission_id,
                "delivery_status": "delivered" if delivered else "queued",
            },
        )
        db.commit()

    return {
        "status": "submitted",
        "submission_id": submission_id,
        "delivery_status": "delivered" if delivered else "queued",
    }


def list_contact_submissions(
    db: Session,
    delivery_status: str | None = None,
) -> list[dict[str, Any]]:
    where_clause = ""
    params: dict[str, Any] = {}
    if delivery_status:
        where_clause = "WHERE delivery_status = :delivery_status"
        params["delivery_status"] = delivery_status

    rows = db.execute(
        text(
            f"""
            SELECT
                submission_id,
                name,
                email,
                subject,
                message,
                delivery_status,
                created_at,
                delivered_at
            FROM contact_submissions
            {where_clause}
            ORDER BY created_at DESC
            """
        ),
        params,
    ).mappings().all()

    return [
        {
            "submission_id": row["submission_id"],
            "name": row["name"],
            "email": row["email"],
            "subject": row["subject"],
            "message": row["message"],
            "delivery_status": row["delivery_status"],
            "created_at": row["created_at"],
            "delivered_at": row["delivered_at"],
        }
        for row in rows
    ]
