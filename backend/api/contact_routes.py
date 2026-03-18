from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.api.rate_limit import build_rate_limit_dependency
from backend.config.settings import RATE_LIMIT_CONTACT_REQUESTS, RATE_LIMIT_CONTACT_WINDOW_SECONDS
from backend.contact.contact_service import ContactServiceError, create_contact_submission
from backend.db.database import get_db


router = APIRouter(tags=["contact"])
contact_rate_limit = build_rate_limit_dependency(
    "contact_submission",
    RATE_LIMIT_CONTACT_REQUESTS,
    RATE_LIMIT_CONTACT_WINDOW_SECONDS,
)


class ContactSubmissionRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=10, max_length=5000)


def _error_response(exc: ContactServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error_code})


@router.post("/contact")
def create_contact_submission_route(
    payload: ContactSubmissionRequest,
    request: Request,
    _: None = Depends(contact_rate_limit),
    db: Session = Depends(get_db),
) -> Any:
    client_ip = request.client.host if request.client else None
    try:
        return create_contact_submission(
            db,
            name=payload.name,
            email=payload.email,
            subject=payload.subject,
            message=payload.message,
            client_ip=client_ip,
        )
    except ContactServiceError as exc:
        return _error_response(exc)
