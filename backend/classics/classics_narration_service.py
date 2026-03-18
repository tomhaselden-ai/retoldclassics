from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.classics.classics_audio_storage import ClassicsAudioStorage
from backend.classics.classics_image_storage import ClassicsImageStorage
from backend.classics.classics_repository import (
    ClassicalStoryRecord,
    list_classical_story_candidates,
    update_classical_story_illustrations,
    update_classical_story_narration,
)
from backend.classics.classics_serializer import ALLOWED_AUTHORS, build_base_read_units, parse_json_like
from backend.narration.polly_client import DEFAULT_VOICE, PollyNarrationClient
from backend.narration.speechmark_parser import parse_speech_marks
from backend.visuals.openai_image_client import OpenAIImageClient


DEFAULT_AUDIO_PADDING_MS = 900


@dataclass
class ClassicsNarrationSummary:
    processed: int = 0
    generated: int = 0
    skipped: int = 0
    narration_generated: int = 0
    illustrations_generated: int = 0


def _has_valid_polly_narration(story: ClassicalStoryRecord, storage: ClassicsAudioStorage) -> bool:
    parsed = parse_json_like(story.narration)
    if not isinstance(parsed, dict):
        return False
    if parsed.get("mode") != "polly":
        return False
    audio_url = parsed.get("audio_url")
    units = parsed.get("units")
    if not isinstance(audio_url, str) or not isinstance(units, list) or not units:
        return False
    return storage.audio_exists(audio_url)


def _has_valid_classics_illustrations(story: ClassicalStoryRecord, storage: ClassicsImageStorage) -> bool:
    parsed = parse_json_like(story.illustration_prompts)
    if not isinstance(parsed, dict) or parsed.get("mode") != "generated":
        return False

    units = parsed.get("units")
    if not isinstance(units, list) or not units:
        return False

    has_image = False
    for item in units:
        if not isinstance(item, dict):
            continue
        image_url = item.get("image_url")
        if not isinstance(image_url, str) or not image_url:
            continue
        if not storage.image_exists(image_url):
            return False
        has_image = True
    return has_image


def _build_story_text(units: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    compiled_parts: list[str] = []
    boundaries: list[dict[str, Any]] = []
    cursor = 0

    for index, unit in enumerate(units):
        text = unit["text"].strip()
        start = cursor
        end = start + len(text)
        boundaries.append(
            {
                "unit_order": unit["unit_order"],
                "unit_id": unit["unit_id"],
                "unit_type": unit.get("unit_type"),
                "start": start,
                "end": end,
                "text": text,
            }
        )
        compiled_parts.append(text)
        cursor = end
        if index < len(units) - 1:
            compiled_parts.append("\n\n")
            cursor += 2

    return "".join(compiled_parts), boundaries


def _map_speech_marks_to_units(
    marks: list[dict[str, Any]],
    boundaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_text = "\n\n".join(boundary["text"] for boundary in boundaries)
    units_by_order = {
        boundary["unit_order"]: {
            "unit_order": boundary["unit_order"],
            "text": boundary["text"],
            "unit_type": boundary.get("unit_type"),
            "audio_start_ms": None,
            "audio_end_ms": None,
            "speech_marks": [],
        }
        for boundary in boundaries
    }

    cursor = 0
    for mark in marks:
        value = mark.get("value")
        mark_type = mark.get("type")
        if mark_type != "word" or not isinstance(value, str) or not value.strip():
            continue
        if "<" in value or ">" in value:
            continue

        lowered_full = full_text.lower()
        lowered_value = value.lower()
        mark_start = lowered_full.find(lowered_value, cursor)
        if mark_start < 0:
            mark_start = lowered_full.find(lowered_value)
        if mark_start < 0:
            continue
        mark_end = mark_start + len(value)
        cursor = mark_end

        for boundary in boundaries:
            if boundary["start"] <= mark_start < boundary["end"]:
                local_mark = {
                    "time": mark.get("time"),
                    "type": mark_type,
                    "start": mark_start - boundary["start"],
                    "end": mark_end - boundary["start"],
                    "value": value,
                }
                units_by_order[boundary["unit_order"]]["speech_marks"].append(local_mark)
                break

    ordered_units = [units_by_order[boundary["unit_order"]] for boundary in boundaries]

    first_times: list[int | None] = []
    for unit in ordered_units:
        unit_times = [
            mark["time"]
            for mark in unit["speech_marks"]
            if isinstance(mark.get("time"), int) and mark.get("type") == "word"
        ]
        start_time = min(unit_times) if unit_times else None
        unit["audio_start_ms"] = start_time
        first_times.append(start_time)

    all_times = [
        mark["time"]
        for mark in marks
        if isinstance(mark.get("time"), int) and mark.get("type") == "word"
    ]
    last_time = max(all_times) if all_times else 0

    for index, unit in enumerate(ordered_units):
        current_start = unit["audio_start_ms"]
        next_start = next(
            (
                later
                for later in first_times[index + 1 :]
                if isinstance(later, int)
            ),
            None,
        )
        if isinstance(current_start, int):
            unit["audio_end_ms"] = (next_start - 1) if isinstance(next_start, int) else last_time + DEFAULT_AUDIO_PADDING_MS

    return ordered_units


def _extract_prompt_text(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("prompt", "prompt_excerpt", "illustration_prompt"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _extract_existing_illustration_prompts(story: ClassicalStoryRecord) -> dict[int, str]:
    parsed = parse_json_like(story.illustration_prompts)
    prompts: dict[int, str] = {}

    if isinstance(parsed, list):
        for index, item in enumerate(parsed):
            prompt = _extract_prompt_text(item)
            if prompt:
                prompts[index] = prompt
    elif isinstance(parsed, dict):
        units = parsed.get("units")
        if isinstance(units, list):
            for index, item in enumerate(units):
                if not isinstance(item, dict):
                    continue
                prompt = _extract_prompt_text(item)
                key = item.get("illustration_key")
                lookup_key = key if isinstance(key, int) else index
                if prompt:
                    prompts[lookup_key] = prompt

    return prompts


def _build_fallback_illustration_prompt(story: ClassicalStoryRecord, unit: dict[str, Any]) -> str:
    scene_title = unit.get("scene_title")
    scene_line = f"Scene title: {scene_title}" if isinstance(scene_title, str) and scene_title.strip() else "Scene title: Untitled moment"
    text_excerpt = unit["text"].strip().replace("\n", " ")[:420]
    author = story.source_author or "Classic"
    title = story.title or "Untitled Story"
    return "\n\n".join(
        [
            "Children's storybook illustration.",
            f"Story title: {title}",
            f"Author collection: {author}",
            scene_line,
            f"Scene text cues: {text_excerpt}",
            "Style: timeless children's book art, expressive characters, warm lighting, clear storytelling, suitable for young readers.",
        ]
    )


def _build_illustration_targets(story: ClassicalStoryRecord) -> list[dict[str, Any]]:
    units = build_base_read_units(story)
    prompt_lookup = _extract_existing_illustration_prompts(story)
    targets: list[dict[str, Any]] = []
    seen_keys: set[int] = set()

    for unit in units:
        if unit.get("unit_type") != "paragraph":
            continue
        illustration_key = unit.get("illustration_key")
        if not isinstance(illustration_key, int) or illustration_key in seen_keys:
            continue
        seen_keys.add(illustration_key)
        prompt = prompt_lookup.get(illustration_key) or _build_fallback_illustration_prompt(story, unit)
        targets.append(
            {
                "illustration_key": illustration_key,
                "scene_title": unit.get("scene_title"),
                "prompt": prompt,
            }
        )

    return targets


def generate_story_illustration_payload(
    story: ClassicalStoryRecord,
    image_client: OpenAIImageClient,
    image_storage: ClassicsImageStorage,
) -> dict[str, Any]:
    targets = _build_illustration_targets(story)
    if not targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classic story has no illustration targets",
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    generated_units: list[dict[str, Any]] = []

    for target in targets:
        image_bytes = image_client.generate_image(target["prompt"])
        image_url = image_storage.save_scene_illustration(
            story.story_id,
            target["illustration_key"],
            image_bytes,
        )
        generated_units.append(
            {
                "illustration_key": target["illustration_key"],
                "scene_title": target.get("scene_title"),
                "prompt": target["prompt"],
                "image_url": image_url,
                "generated_at": generated_at,
            }
        )

    return {
        "mode": "generated",
        "generated_at": generated_at,
        "units": generated_units,
    }


def generate_story_narration_payload(
    story: ClassicalStoryRecord,
    voice: str,
    polly_client: PollyNarrationClient,
    audio_storage: ClassicsAudioStorage,
) -> dict[str, Any]:
    units = build_base_read_units(story)
    if not units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classic story has no readable units for narration",
        )

    full_text, boundaries = _build_story_text(units)
    synthesis = polly_client.synthesize_storytelling_narration(
        full_text,
        style_mode="classic_read_aloud",
        pronunciation_overrides=None,
        requires_speech_marks=True,
        preferred_voice_id=voice,
    )
    speech_marks = parse_speech_marks(synthesis.speech_marks_raw)
    unit_payload = _map_speech_marks_to_units(speech_marks, boundaries)
    audio_url = audio_storage.save_story_audio(story.story_id, synthesis.audio_bytes)

    return {
        "mode": "polly",
        "voice": synthesis.voice_plan.voice_id,
        "engine": synthesis.voice_plan.engine,
        "sample_rate": synthesis.voice_plan.sample_rate,
        "output_format": synthesis.voice_plan.output_format,
        "audio_url": audio_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "units": unit_payload,
    }


def generate_classics_narration(
    db: Session,
    author: str | None = None,
    story_id: int | None = None,
    limit: int | None = None,
    sort_order: str = "author",
    force: bool = False,
    voice: str = DEFAULT_VOICE,
    progress_callback: Callable[[ClassicalStoryRecord, str], None] | None = None,
) -> ClassicsNarrationSummary:
    if author is not None and author not in ALLOWED_AUTHORS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported classics author")

    authors = [author] if author else list(ALLOWED_AUTHORS)
    audio_storage = ClassicsAudioStorage()
    image_storage = ClassicsImageStorage()
    polly_client = PollyNarrationClient()
    image_client: OpenAIImageClient | None = None
    summary = ClassicsNarrationSummary()

    stories = list_classical_story_candidates(
        db,
        authors=authors,
        story_id=story_id,
        limit=limit,
        sort_order=sort_order,
    )

    try:
        for story in stories:
            summary.processed += 1
            story_updated = False

            if force or not _has_valid_polly_narration(story, audio_storage):
                narration_payload = generate_story_narration_payload(
                    story=story,
                    voice=voice,
                    polly_client=polly_client,
                    audio_storage=audio_storage,
                )
                update_classical_story_narration(db, story.story_id, narration_payload)
                summary.narration_generated += 1
                story_updated = True

            if force or not _has_valid_classics_illustrations(story, image_storage):
                if image_client is None:
                    image_client = OpenAIImageClient()
                illustration_payload = generate_story_illustration_payload(
                    story=story,
                    image_client=image_client,
                    image_storage=image_storage,
                )
                update_classical_story_illustrations(db, story.story_id, illustration_payload)
                summary.illustrations_generated += 1
                story_updated = True

            if story_updated:
                db.commit()
                summary.generated += 1
                if progress_callback is not None:
                    progress_callback(story, "generated")
            else:
                summary.skipped += 1
                if progress_callback is not None:
                    progress_callback(story, "skipped")

        return summary
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Classics narration generation failed",
        ) from exc
