from __future__ import annotations

import re
from dataclasses import dataclass

from backend.narration.voice_strategy import SUPPORTED_STYLES


@dataclass(frozen=True)
class NarrationSentence:
    text: str


@dataclass(frozen=True)
class NarrationParagraph:
    text: str
    role: str
    sentences: list[NarrationSentence]


@dataclass(frozen=True)
class NarrationDocument:
    style_mode: str
    paragraphs: list[NarrationParagraph]


SUSPENSE_MARKERS = ("suddenly", "at that moment", "without warning", "but then", "to their surprise", "finally")
ACTION_MARKERS = ("ran", "rushed", "leapt", "jumped", "hurried", "cried", "shouted")
BEDTIME_MARKERS = ("moon", "night", "sleep", "dream", "soft", "quiet", "gentle", "stars")
MORAL_MARKERS = ("lesson", "remember", "wise", "important", "kindness", "should", "never", "always")


def _split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]
    return paragraphs or [normalized]


def _split_sentences(text: str) -> list[str]:
    spaced = re.sub(r"([?!])\"", r'\1 "', text)
    parts = re.split(r"(?<=[.!?])\s+", spaced)
    sentences = [part.strip() for part in parts if part.strip()]
    return sentences or [text.strip()]


def _role_for_paragraph(text: str, index: int, total: int, style_mode: str) -> str:
    lowered = text.lower()
    quote_count = text.count('"') + text.count("“") + text.count("”")
    if index == total - 1 and any(marker in lowered for marker in MORAL_MARKERS):
        return "moral"
    if any(marker in lowered for marker in SUSPENSE_MARKERS) or "..." in text:
        return "suspense"
    if any(marker in lowered for marker in ACTION_MARKERS) or "!" in text:
        return "action"
    if quote_count >= 2:
        return "dialogue"
    if style_mode == "bedtime" or any(marker in lowered for marker in BEDTIME_MARKERS):
        return "bedtime"
    return "narration"


def build_narration_document(text: str, style_mode: str) -> NarrationDocument:
    normalized_style = style_mode if style_mode in SUPPORTED_STYLES else "classic_read_aloud"
    paragraphs = _split_paragraphs(text)
    paragraph_nodes: list[NarrationParagraph] = []

    for index, paragraph in enumerate(paragraphs):
        sentences = [NarrationSentence(text=item) for item in _split_sentences(paragraph)]
        paragraph_nodes.append(
            NarrationParagraph(
                text=paragraph,
                role=_role_for_paragraph(paragraph, index, len(paragraphs), normalized_style),
                sentences=sentences,
            )
        )

    return NarrationDocument(style_mode=normalized_style, paragraphs=paragraph_nodes)
