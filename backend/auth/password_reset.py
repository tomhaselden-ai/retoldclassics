import logging
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.auth_service import get_account_by_email, update_password
from backend.config.settings import (
    FRONTEND_APP_URL,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
    is_production_env,
)
from backend.auth.token_manager import create_reset_token, decode_token


logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, reset_token: str) -> None:
    reset_url = f"{FRONTEND_APP_URL}/reset-password/confirm?token={reset_token}"

    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        if is_production_env():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset email is not configured",
            )
        logger.warning("SMTP is not configured; password reset link for %s: %s", email, reset_url)
        return

    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = email
    message["Subject"] = "Reset your Persistent Story Universe password"
    message.set_content(
        "\n".join(
            [
                "A password reset was requested for your account.",
                "",
                "Open the link below to choose a new password:",
                reset_url,
                "",
                "If you did not request this, you can ignore this email.",
            ]
        )
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    except Exception as exc:
        logger.exception("Failed to deliver password reset email to %s", email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send password reset email",
        ) from exc


def create_password_reset_token(db: Session, email: str) -> str:
    account = get_account_by_email(db, email)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    reset_token = create_reset_token(account.account_id, account.email)
    send_password_reset_email(account.email, reset_token)
    return reset_token


def reset_password_with_token(db: Session, reset_token: str, new_password: str) -> None:
    payload = decode_token(reset_token)
    if payload.get("token_type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    account = get_account_by_email(db, email)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    update_password(db, account, new_password)
