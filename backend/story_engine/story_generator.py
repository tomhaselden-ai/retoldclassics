import json
import logging
import os
from typing import Any

import requests
from fastapi import HTTPException, status

from backend.config.settings import OPENAI_API_KEY


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _extract_json_payload(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI returned invalid JSON",
        ) from exc


def generate_story(prompt_messages: list[dict[str, str]]) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured",
        )

    logging.info("Calling OpenAI story generator")
    response = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "response_format": {"type": "json_object"},
            "messages": prompt_messages,
            "temperature": 0.8,
        },
        timeout=30,
    )

    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API failed: {response.text}",
        )

    content = response.json()["choices"][0]["message"]["content"]
    payload = _extract_json_payload(content)

    if "title" not in payload or "scenes" not in payload:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI response is missing required story fields",
        )

    return payload
