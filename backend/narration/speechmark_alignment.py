from __future__ import annotations

import json
from typing import Any


_CHAR_TRANSLATIONS = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
)


def _canonicalize(text: str) -> str:
    return text.translate(_CHAR_TRANSLATIONS)


def coerce_speech_marks(raw_speech_marks: Any) -> list[dict[str, Any]]:
    if raw_speech_marks is None:
        return []

    parsed = raw_speech_marks
    if isinstance(raw_speech_marks, str):
        stripped = raw_speech_marks.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return []

    if not isinstance(parsed, list):
        return []

    return [item for item in parsed if isinstance(item, dict)]


def _find_value_range(
    visible_text: str,
    canonical_text: str,
    value: str,
    cursor: int,
) -> tuple[int, int] | None:
    if not value:
        return None

    canonical_value = _canonicalize(value)
    search_offsets = [cursor, max(0, cursor - 2), max(0, cursor - 8), 0]
    attempted: set[int] = set()

    for offset in search_offsets:
        if offset in attempted:
            continue
        attempted.add(offset)
        found = canonical_text.find(canonical_value, offset)
        while found >= 0:
            end = found + len(canonical_value)
            before_ok = found == 0 or not canonical_text[found - 1].isalnum() or not canonical_value[0].isalnum()
            after_ok = end >= len(canonical_text) or not canonical_text[end].isalnum() or not canonical_value[-1].isalnum()
            if before_ok and after_ok:
                return found, end
            found = canonical_text.find(canonical_value, found + 1)

    lowered_text = canonical_text.lower()
    lowered_value = canonical_value.lower()
    for offset in search_offsets:
        found = lowered_text.find(lowered_value, offset)
        while found >= 0:
            end = found + len(lowered_value)
            before_ok = found == 0 or not lowered_text[found - 1].isalnum() or not lowered_value[0].isalnum()
            after_ok = end >= len(lowered_text) or not lowered_text[end].isalnum() or not lowered_value[-1].isalnum()
            if before_ok and after_ok:
                return found, end
            found = lowered_text.find(lowered_value, found + 1)

    return None


def normalize_speech_marks_for_text(visible_text: str, raw_speech_marks: Any) -> list[dict[str, Any]]:
    marks = coerce_speech_marks(raw_speech_marks)
    if not visible_text or not marks:
        return marks

    canonical_text = _canonicalize(visible_text)
    word_cursor = 0
    sentence_cursor = 0
    normalized: list[dict[str, Any]] = []

    for mark in marks:
        cloned = dict(mark)
        value = cloned.get("value")
        if not isinstance(value, str) or not value:
            normalized.append(cloned)
            continue

        if cloned.get("type") == "word":
            located = _find_value_range(visible_text, canonical_text, value, word_cursor)
            if located is not None:
                start, end = located
                cloned["start"] = start
                cloned["end"] = end
                word_cursor = end
        elif cloned.get("type") == "sentence":
            located = _find_value_range(visible_text, canonical_text, value, sentence_cursor)
            if located is not None:
                start, end = located
                cloned["start"] = start
                cloned["end"] = end
                sentence_cursor = end

        normalized.append(cloned)

    return normalized
