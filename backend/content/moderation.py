from fastapi import Depends, HTTPException, status

from backend.auth.token_manager import get_current_account
from backend.config.settings import CONTENT_ADMIN_EMAILS


def require_content_moderator(current_account=Depends(get_current_account)):
    email = (getattr(current_account, "email", "") or "").strip().lower()
    if email not in CONTENT_ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content moderation requires an approved studio account",
        )
    return current_account
