import json
import re


STOP_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "along",
    "also",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "back",
    "be",
    "because",
    "been",
    "before",
    "but",
    "by",
    "came",
    "can",
    "could",
    "did",
    "do",
    "down",
    "for",
    "from",
    "get",
    "got",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "like",
    "little",
    "made",
    "make",
    "many",
    "me",
    "more",
    "most",
    "much",
    "must",
    "my",
    "never",
    "no",
    "not",
    "now",
    "of",
    "off",
    "on",
    "one",
    "only",
    "or",
    "other",
    "our",
    "out",
    "over",
    "said",
    "saw",
    "she",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "too",
    "under",
    "up",
    "upon",
    "us",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "would",
    "you",
    "your",
}


def extract_story_text(scene_text: str | None) -> str:
    if scene_text is None or not scene_text.strip():
        return ""

    try:
        payload = json.loads(scene_text)
    except json.JSONDecodeError:
        return scene_text

    parts: list[str] = []
    paragraphs = payload.get("paragraphs")
    if isinstance(paragraphs, list):
        parts.extend(part for part in paragraphs if isinstance(part, str))

    embedded_scene_text = payload.get("scene_text")
    if isinstance(embedded_scene_text, str):
        parts.append(embedded_scene_text)

    if not parts:
        return scene_text
    return "\n".join(parts)


def calculate_difficulty_level(word: str, reading_level: str | None) -> int:
    base = 1
    length = len(word)

    if length >= 10:
        base = 3
    elif length >= 7:
        base = 2

    if reading_level:
        lowered = reading_level.lower()
        if "grade 1" in lowered or "grade 2" in lowered:
            return min(base + 1, 3)

    return base


def extract_vocabulary_words(scene_texts: list[str], reading_level: str | None) -> list[dict[str, int | str]]:
    text = "\n".join(extract_story_text(scene_text) for scene_text in scene_texts)
    candidates = re.findall(r"[A-Za-z][A-Za-z'-]{4,}", text.lower())

    words: list[dict[str, int | str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        word = candidate.strip("-'")
        if len(word) < 5 or word in STOP_WORDS or word in seen:
            continue
        seen.add(word)
        words.append(
            {
                "word": word,
                "difficulty_level": calculate_difficulty_level(word, reading_level),
            }
        )

    return words
