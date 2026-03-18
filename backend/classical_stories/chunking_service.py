import json
import re
from pathlib import Path
from typing import Any

from backend.classical_stories.source_repository import SourceStoryRecord


CHUNK_TARGET_TOKENS = 425
CHUNK_MIN_TOKENS = 350
CHUNK_MAX_TOKENS = 500
CHUNK_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "classical_story_chunks.json"
)


def _normalize_json_field(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _extract_paragraph_texts(paragraphs_modern: Any) -> list[str]:
    normalized = _normalize_json_field(paragraphs_modern)

    if isinstance(normalized, list):
        texts: list[str] = []
        for item in normalized:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
            elif isinstance(item, str) and item.strip():
                texts.append(item.strip())
        return texts

    if isinstance(normalized, str) and normalized.strip():
        return [normalized.strip()]

    return []


def _estimate_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text))


def build_story_chunks(destination_story_id: int, story: SourceStoryRecord) -> list[dict[str, Any]]:
    paragraphs = _extract_paragraph_texts(story.paragraphs_modern)
    if not paragraphs:
        return []

    chunks: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = _estimate_tokens(paragraph)
        projected_tokens = current_tokens + paragraph_tokens

        if current_parts and projected_tokens > CHUNK_MAX_TOKENS:
            chunks.append(
                {
                    "story_id": destination_story_id,
                    "title": story.title,
                    "author": story.source_author,
                    "themes": story.themes,
                    "text_chunk": "\n\n".join(current_parts),
                }
            )
            current_parts = [paragraph]
            current_tokens = paragraph_tokens
            continue

        current_parts.append(paragraph)
        current_tokens = projected_tokens

        if current_tokens >= CHUNK_TARGET_TOKENS and current_tokens >= CHUNK_MIN_TOKENS:
            chunks.append(
                {
                    "story_id": destination_story_id,
                    "title": story.title,
                    "author": story.source_author,
                    "themes": story.themes,
                    "text_chunk": "\n\n".join(current_parts),
                }
            )
            current_parts = []
            current_tokens = 0

    if current_parts:
        if chunks and current_tokens < CHUNK_MIN_TOKENS:
            trailing_text = "\n\n".join(current_parts)
            chunks[-1]["text_chunk"] = (
                f"{chunks[-1]['text_chunk']}\n\n{trailing_text}"
            )
        else:
            chunks.append(
                {
                    "story_id": destination_story_id,
                    "title": story.title,
                    "author": story.source_author,
                    "themes": story.themes,
                    "text_chunk": "\n\n".join(current_parts),
                }
            )

    return chunks


def write_chunks(chunks: list[dict[str, Any]]) -> None:
    CHUNK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHUNK_OUTPUT_PATH.open("w", encoding="utf-8") as file_handle:
        json.dump(chunks, file_handle, ensure_ascii=False, indent=2)
