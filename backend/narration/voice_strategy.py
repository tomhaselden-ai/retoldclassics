from __future__ import annotations

from dataclasses import dataclass

from backend.config.settings import (
    POLLY_DEFAULT_VOICE,
    POLLY_ENABLE_SPEECH_MARKS,
    POLLY_ENGINE_PRIORITY,
    POLLY_GENERATIVE_VOICE,
    POLLY_LONG_FORM_VOICE,
    POLLY_NEURAL_VOICE,
    POLLY_OUTPUT_FORMAT,
    POLLY_SAMPLE_RATE,
    POLLY_STANDARD_VOICE,
)


SUPPORTED_ENGINES = ("generative", "long-form", "neural", "standard")
SUPPORTED_STYLES = ("bedtime", "classic_read_aloud", "playful_adventure", "dramatic_intro")


DEFAULT_ENGINE_VOICES = {
    "generative": POLLY_GENERATIVE_VOICE,
    "long-form": POLLY_LONG_FORM_VOICE,
    "neural": POLLY_NEURAL_VOICE,
    "standard": POLLY_STANDARD_VOICE,
}

ENGINES_WITH_SPEECH_MARK_SUPPORT = {"standard", "neural", "long-form"}


@dataclass(frozen=True)
class VoicePlan:
    engine: str
    voice_id: str
    sample_rate: str
    output_format: str
    text_type: str = "ssml"
    style_mode: str = "classic_read_aloud"


def _parse_engine_priority() -> list[str]:
    parsed = [
        item.strip().lower()
        for item in POLLY_ENGINE_PRIORITY.split(",")
        if item.strip()
    ]
    candidates = [engine for engine in parsed if engine in SUPPORTED_ENGINES]
    if not candidates:
        return ["long-form", "neural", "standard"]
    return candidates


def _resolve_voice_for_engine(engine: str) -> str:
    if POLLY_DEFAULT_VOICE:
        return POLLY_DEFAULT_VOICE
    return DEFAULT_ENGINE_VOICES.get(engine, POLLY_STANDARD_VOICE)


def choose_voice_plan(
    style_mode: str,
    requires_speech_marks: bool = True,
    preferred_voice_id: str | None = None,
) -> VoicePlan:
    normalized_style = style_mode if style_mode in SUPPORTED_STYLES else "classic_read_aloud"
    engine_candidates = _parse_engine_priority()

    for engine in engine_candidates:
        if requires_speech_marks and POLLY_ENABLE_SPEECH_MARKS and engine not in ENGINES_WITH_SPEECH_MARK_SUPPORT:
            continue
        return VoicePlan(
            engine=engine,
            voice_id=preferred_voice_id or _resolve_voice_for_engine(engine),
            sample_rate=POLLY_SAMPLE_RATE,
            output_format=POLLY_OUTPUT_FORMAT,
            text_type="ssml",
            style_mode=normalized_style,
        )

    return VoicePlan(
        engine="standard",
        voice_id=preferred_voice_id or _resolve_voice_for_engine("standard"),
        sample_rate=POLLY_SAMPLE_RATE,
        output_format=POLLY_OUTPUT_FORMAT,
        text_type="ssml",
        style_mode=normalized_style,
    )


def list_voice_plan_candidates(
    style_mode: str,
    requires_speech_marks: bool = True,
    preferred_voice_id: str | None = None,
) -> list[VoicePlan]:
    normalized_style = style_mode if style_mode in SUPPORTED_STYLES else "classic_read_aloud"
    plans: list[VoicePlan] = []
    seen: set[tuple[str, str]] = set()

    for engine in _parse_engine_priority():
        if requires_speech_marks and POLLY_ENABLE_SPEECH_MARKS and engine not in ENGINES_WITH_SPEECH_MARK_SUPPORT:
            continue

        candidate_voices: list[str] = []
        if preferred_voice_id:
            candidate_voices.append(preferred_voice_id)
        resolved_voice = _resolve_voice_for_engine(engine)
        if resolved_voice not in candidate_voices:
            candidate_voices.append(resolved_voice)

        for voice_id in candidate_voices:
            key = (engine, voice_id)
            if key in seen:
                continue
            seen.add(key)
            plans.append(
                VoicePlan(
                    engine=engine,
                    voice_id=voice_id,
                    sample_rate=POLLY_SAMPLE_RATE,
                    output_format=POLLY_OUTPUT_FORMAT,
                    text_type="ssml",
                    style_mode=normalized_style,
                )
            )

    if not plans:
        plans.append(
            VoicePlan(
                engine="standard",
                voice_id=preferred_voice_id or _resolve_voice_for_engine("standard"),
                sample_rate=POLLY_SAMPLE_RATE,
                output_format=POLLY_OUTPUT_FORMAT,
                text_type="ssml",
                style_mode=normalized_style,
            )
        )

    return plans
