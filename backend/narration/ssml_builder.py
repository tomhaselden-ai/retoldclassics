from __future__ import annotations

from dataclasses import dataclass

from backend.narration.pronunciation import PronunciationRule, apply_pronunciation_rules
from backend.narration.text_preprocessor import NarrationDocument, NarrationParagraph


@dataclass(frozen=True)
class ParagraphDelivery:
    rate: str
    volume: str | None
    break_before_ms: int
    break_after_ms: int


STYLE_BASELINES = {
    "bedtime": {"rate": 92, "volume": "soft"},
    "classic_read_aloud": {"rate": 100, "volume": None},
    "playful_adventure": {"rate": 104, "volume": None},
    "dramatic_intro": {"rate": 96, "volume": None},
}

ROLE_ADJUSTMENTS = {
    "narration": {"rate": 0, "before": 0, "after": 260, "volume": None},
    "dialogue": {"rate": 4, "before": 0, "after": 180, "volume": None},
    "action": {"rate": 6, "before": 0, "after": 140, "volume": "medium"},
    "suspense": {"rate": -8, "before": 500, "after": 420, "volume": None},
    "moral": {"rate": -10, "before": 400, "after": 560, "volume": "soft"},
    "bedtime": {"rate": -10, "before": 240, "after": 420, "volume": "soft"},
}


def _delivery_for_paragraph(style_mode: str, paragraph: NarrationParagraph) -> ParagraphDelivery:
    baseline = STYLE_BASELINES.get(style_mode, STYLE_BASELINES["classic_read_aloud"])
    adjustment = ROLE_ADJUSTMENTS.get(paragraph.role, ROLE_ADJUSTMENTS["narration"])
    rate_value = max(82, min(112, baseline["rate"] + adjustment["rate"]))
    volume_value = adjustment["volume"] or baseline["volume"]
    return ParagraphDelivery(
        rate=f"{rate_value}%",
        volume=volume_value,
        break_before_ms=adjustment["before"],
        break_after_ms=adjustment["after"],
    )


def _wrap_sentence(text: str, delivery: ParagraphDelivery, pronunciation_rules: dict[str, PronunciationRule]) -> str:
    escaped_text = apply_pronunciation_rules(text, pronunciation_rules)
    if delivery.volume:
        return f'<s><prosody rate="{delivery.rate}" volume="{delivery.volume}">{escaped_text}</prosody></s>'
    return f'<s><prosody rate="{delivery.rate}">{escaped_text}</prosody></s>'


def build_storytelling_ssml(
    document: NarrationDocument,
    pronunciation_rules: dict[str, PronunciationRule] | None = None,
) -> str:
    rules = pronunciation_rules or {}
    paragraph_fragments: list[str] = []

    for paragraph in document.paragraphs:
        delivery = _delivery_for_paragraph(document.style_mode, paragraph)
        pieces: list[str] = []
        if delivery.break_before_ms > 0:
            pieces.append(f'<break time="{delivery.break_before_ms}ms"/>')
        sentence_fragments = [
            _wrap_sentence(sentence.text, delivery, rules)
            for sentence in paragraph.sentences
            if sentence.text.strip()
        ]
        pieces.append("<p>")
        pieces.extend(sentence_fragments)
        if delivery.break_after_ms > 0:
            pieces.append(f'<break time="{delivery.break_after_ms}ms"/>')
        pieces.append("</p>")
        paragraph_fragments.append("".join(pieces))

    return f"<speak>{''.join(paragraph_fragments)}</speak>"
