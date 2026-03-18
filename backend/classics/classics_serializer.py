import json
from collections import defaultdict
from typing import Any

from backend.classics.classics_repository import ClassicalStoryRecord


ALLOWED_AUTHORS = ("Andersen", "Grimm", "Bible", "Aesop")

AUTHOR_ALIASES = {
    "andersen": "Andersen",
    "hans christian andersen": "Andersen",
    "grimm": "Grimm",
    "brothers grimm": "Grimm",
    "bible": "Bible",
    "the children's bible": "Bible",
    "the childrens bible": "Bible",
    "aesop": "Aesop",
}

AUTHOR_FILTER_VALUES = {
    "Andersen": ["Andersen", "Hans Christian Andersen"],
    "Grimm": ["Grimm", "Brothers Grimm"],
    "Bible": ["Bible", "The Children's Bible"],
    "Aesop": ["Aesop"],
}

AUTHOR_ACCENT_TOKENS = {
    "Andersen": "aurora-cyan",
    "Grimm": "ember-gold",
    "Bible": "starlight-blue",
    "Aesop": "sunrise-coral",
}

DISPLAY_TITLES = {
    "Andersen": "Andersen",
    "Grimm": "Grimm",
    "Bible": "Bible",
    "Aesop": "Aesop",
}


def normalize_author(author: str | None) -> str | None:
    if not author:
        return None
    lowered = author.strip().lower()
    return AUTHOR_ALIASES.get(lowered)


def expand_author_filters(authors: list[str]) -> list[str]:
    values: list[str] = []
    for author in authors:
        for candidate in AUTHOR_FILTER_VALUES.get(author, [author]):
            if candidate not in values:
                values.append(candidate)
    return values


def parse_json_like(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value
    return value


def build_cover_metadata(story: ClassicalStoryRecord) -> dict[str, Any]:
    author = normalize_author(story.source_author) or "Classics"
    illustration_lookup = _build_illustration_lookup(story.illustration_prompts)
    first_illustration = next(
        (
            item.get("image_url")
            for _, item in sorted(illustration_lookup.items())
            if isinstance(item.get("image_url"), str) and item.get("image_url")
        ),
        None,
    )
    return {
        "mode": "generated" if first_illustration else "typographic_only",
        "image_url": first_illustration,
        "accent_token": AUTHOR_ACCENT_TOKENS.get(author, "aurora-cyan"),
        "display_title": story.title or "Untitled Story",
    }


def has_playable_narration(story: ClassicalStoryRecord) -> bool:
    parsed = parse_json_like(getattr(story, "narration", None))
    if not isinstance(parsed, dict):
        return False
    audio_url = parsed.get("audio_url")
    return isinstance(audio_url, str) and bool(audio_url.strip())


def _extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        for key in ("text", "paragraph", "content", "scene_text", "summary"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


def _extract_read_text(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        for key in ("text", "paragraph", "content", "scene_text"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


def extract_preview_text(story: ClassicalStoryRecord) -> str:
    paragraphs = parse_json_like(story.paragraphs_modern)
    if isinstance(paragraphs, list):
        for item in paragraphs:
            text = _extract_text(item)
            if text:
                return text[:220]

    scenes = parse_json_like(story.scenes)
    if isinstance(scenes, list):
        for item in scenes:
            text = _extract_text(item)
            if text:
                return text[:220]
            if isinstance(item, dict) and isinstance(item.get("paragraphs"), list):
                for paragraph in item["paragraphs"]:
                    text = _extract_text(paragraph)
                    if text:
                        return text[:220]

    if story.moral and story.moral.strip():
        return story.moral.strip()[:220]
    return "A classic story ready for immersive reading."


def _coerce_string_list(value: Any) -> list[str]:
    parsed = parse_json_like(value)
    if isinstance(parsed, list):
        results: list[str] = []
        for item in parsed:
            text = _extract_text(item)
            if text:
                results.append(text)
        return results
    text = _extract_text(parsed)
    return [text] if text else []


def build_base_read_units(story: ClassicalStoryRecord) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    unit_order = 1
    illustration_lookup = _build_illustration_lookup(story.illustration_prompts)
    title_text = (story.title or "Untitled Story").strip()

    if title_text:
        units.append(
            {
                "unit_id": f"classic-{story.story_id}-title",
                "unit_order": unit_order,
                "unit_type": "title",
                "scene_title": None,
                "text": title_text,
                "illustration_key": None,
                "narration_text": None,
                "audio_start_ms": None,
                "audio_end_ms": None,
                "speech_marks": [],
                "illustration": {
                    "mode": "typographic_only",
                    "image_url": None,
                    "prompt_excerpt": None,
                },
            }
        )
        unit_order += 1

    scenes = parse_json_like(story.scenes)
    if isinstance(scenes, list):
        scene_has_readable_text = False
        for scene_index, scene in enumerate(scenes):
            scene_title = None
            paragraphs: list[str] = []

            if isinstance(scene, dict):
                for key in ("title", "scene_title", "name"):
                    value = scene.get(key)
                    if isinstance(value, str) and value.strip():
                        scene_title = value.strip()
                        break

                if isinstance(scene.get("paragraphs"), list):
                    paragraphs = [text for text in (_extract_read_text(item) for item in scene["paragraphs"]) if text]
                else:
                    text = _extract_read_text(scene)
                    if text:
                        paragraphs = [text]
            else:
                text = _extract_read_text(scene)
                if text:
                    paragraphs = [text]

            for paragraph in paragraphs:
                scene_has_readable_text = True
                units.append(
                    {
                        "unit_id": f"classic-{story.story_id}-{unit_order}",
                        "unit_order": unit_order,
                        "unit_type": "paragraph",
                        "scene_title": scene_title,
                        "text": paragraph,
                        "illustration_key": scene_index,
                        "narration_text": None,
                        "audio_start_ms": None,
                        "audio_end_ms": None,
                        "speech_marks": [],
                        "illustration": {
                            "mode": (
                                "generated"
                                if illustration_lookup.get(scene_index, {}).get("image_url")
                                else "prompt_derived"
                                if illustration_lookup.get(scene_index)
                                else "typographic_only"
                            ),
                            "image_url": illustration_lookup.get(scene_index, {}).get("image_url"),
                            "prompt_excerpt": illustration_lookup.get(scene_index, {}).get("prompt_excerpt"),
                        },
                    }
                )
                unit_order += 1

        if not scene_has_readable_text:
            units = units[:1]
            unit_order = 2

    if len(units) == 1:
        for paragraph in _coerce_string_list(story.paragraphs_modern):
            units.append(
                {
                    "unit_id": f"classic-{story.story_id}-{unit_order}",
                    "unit_order": unit_order,
                    "unit_type": "paragraph",
                    "scene_title": None,
                    "text": paragraph,
                    "illustration_key": unit_order - 2,
                    "narration_text": None,
                    "audio_start_ms": None,
                    "audio_end_ms": None,
                    "speech_marks": [],
                    "illustration": {
                        "mode": (
                            "generated"
                            if illustration_lookup.get(unit_order - 2, {}).get("image_url")
                            else "prompt_derived"
                            if illustration_lookup.get(unit_order - 2)
                            else "typographic_only"
                        ),
                        "image_url": illustration_lookup.get(unit_order - 2, {}).get("image_url"),
                        "prompt_excerpt": illustration_lookup.get(unit_order - 2, {}).get("prompt_excerpt"),
                    },
                }
            )
            unit_order += 1

    return units


def build_shelf_payload(stories: list[ClassicalStoryRecord], total_count: int) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for story in stories:
        author = normalize_author(story.source_author)
        if author is None:
            continue
        groups[author].append(
            {
                "story_id": story.story_id,
                "title": story.title,
                "source_author": author,
                "age_range": story.age_range,
                "reading_level": story.reading_level,
                "preview_text": extract_preview_text(story),
                "cover": build_cover_metadata(story),
                "immersive_reader_available": True,
                "narration_available": has_playable_narration(story),
            }
        )

    return {
        "groups": [
            {
                "author": author,
                "items": groups.get(author, []),
            }
            for author in ALLOWED_AUTHORS
            if groups.get(author)
        ],
        "total_count": total_count,
    }


def build_story_detail_payload(story: ClassicalStoryRecord) -> dict[str, Any]:
    return {
        "story_id": story.story_id,
        "title": story.title,
        "source_author": normalize_author(story.source_author),
        "source_story_id": story.source_story_id,
        "age_range": story.age_range,
        "reading_level": story.reading_level,
        "moral": story.moral,
        "characters": parse_json_like(story.characters),
        "locations": parse_json_like(story.locations),
        "traits": parse_json_like(story.traits),
        "themes": parse_json_like(story.themes),
        "cover": build_cover_metadata(story),
        "summary": extract_preview_text(story),
        "immersive_reader_available": True,
    }


def _build_narration_lookup(narration_value: Any) -> tuple[dict[int, str], str | None]:
    parsed = parse_json_like(narration_value)
    per_unit: dict[int, str] = {}
    story_level: str | None = None

    if isinstance(parsed, list):
        for index, item in enumerate(parsed):
            text = _extract_text(item)
            if text:
                per_unit[index] = text
    elif isinstance(parsed, dict):
        story_level = _extract_text(parsed)
        units = parsed.get("units")
        if isinstance(units, list):
            for index, item in enumerate(units):
                text = _extract_text(item)
                if text:
                    per_unit[index] = text
    elif isinstance(parsed, str):
        story_level = parsed

    return per_unit, story_level


def _apply_narration_payload(units: list[dict[str, Any]], narration_value: Any) -> dict[str, Any]:
    parsed = parse_json_like(narration_value)
    narration_meta = {
        "audio_url": None,
        "voice": None,
        "generated_at": None,
        "available": False,
    }

    if isinstance(parsed, dict) and parsed.get("mode") == "polly":
        unit_lookup = {
            int(item["unit_order"]): item
            for item in parsed.get("units", [])
            if isinstance(item, dict) and isinstance(item.get("unit_order"), int)
        }
        for unit in units:
            payload = unit_lookup.get(unit["unit_order"])
            if not payload:
                continue
            unit["narration_text"] = payload.get("text") if isinstance(payload.get("text"), str) else unit["text"]
            unit["audio_start_ms"] = payload.get("audio_start_ms") if isinstance(payload.get("audio_start_ms"), int) else None
            unit["audio_end_ms"] = payload.get("audio_end_ms") if isinstance(payload.get("audio_end_ms"), int) else None
            speech_marks = payload.get("speech_marks")
            unit["speech_marks"] = speech_marks if isinstance(speech_marks, list) else []

        audio_url = parsed.get("audio_url")
        voice = parsed.get("voice")
        generated_at = parsed.get("generated_at")
        narration_meta = {
            "audio_url": audio_url if isinstance(audio_url, str) else None,
            "voice": voice if isinstance(voice, str) else None,
            "generated_at": generated_at if isinstance(generated_at, str) else None,
            "available": isinstance(audio_url, str),
        }
        return narration_meta

    narration_lookup, story_level_narration = _build_narration_lookup(narration_value)
    for unit in units:
        unit["narration_text"] = narration_lookup.get(unit["unit_order"] - 1) or story_level_narration

    return narration_meta


def _extract_illustration_prompt(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("prompt", "prompt_excerpt", "illustration_prompt"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()[:180]
    return _extract_text(value)


def _build_illustration_lookup(illustration_value: Any) -> dict[int, dict[str, Any]]:
    parsed = parse_json_like(illustration_value)
    lookup: dict[int, dict[str, Any]] = {}
    if isinstance(parsed, list):
        for index, item in enumerate(parsed):
            prompt_excerpt = _extract_illustration_prompt(item)
            image_url = item.get("image_url") if isinstance(item, dict) and isinstance(item.get("image_url"), str) else None
            if prompt_excerpt or image_url:
                lookup[index] = {
                    "prompt_excerpt": prompt_excerpt[:180] if isinstance(prompt_excerpt, str) else None,
                    "image_url": image_url,
                }
    elif isinstance(parsed, dict):
        units = parsed.get("units")
        if isinstance(units, list):
            for index, item in enumerate(units):
                prompt_excerpt = _extract_illustration_prompt(item)
                image_url = item.get("image_url") if isinstance(item, dict) and isinstance(item.get("image_url"), str) else None
                key = item.get("illustration_key") if isinstance(item, dict) else None
                lookup_key = key if isinstance(key, int) else index
                if prompt_excerpt or image_url:
                    lookup[lookup_key] = {
                        "prompt_excerpt": prompt_excerpt[:180] if isinstance(prompt_excerpt, str) else None,
                        "image_url": image_url,
                    }
    return lookup


def build_read_payload(story: ClassicalStoryRecord) -> dict[str, Any]:
    units = build_base_read_units(story)
    if not units or all(unit.get("unit_type") == "title" for unit in units):
        raise ValueError("unreadable_classic_story")
    narration_meta = _apply_narration_payload(units, story.narration)

    return {
        "story_id": story.story_id,
        "title": story.title,
        "source_author": normalize_author(story.source_author),
        "age_range": story.age_range,
        "reading_level": story.reading_level,
        "cover": build_cover_metadata(story),
        "reader_mode": "immersive",
        "has_scene_groups": any(unit["scene_title"] for unit in units),
        "has_paragraphs": any(unit.get("unit_type") == "paragraph" for unit in units),
        "has_narration_text": any(unit["narration_text"] for unit in units),
        "audio_url": narration_meta["audio_url"],
        "voice": narration_meta["voice"],
        "generated_at": narration_meta["generated_at"],
        "narration_available": narration_meta["available"],
        "units": units,
        "moral": story.moral,
        "characters": parse_json_like(story.characters),
        "locations": parse_json_like(story.locations),
        "traits": parse_json_like(story.traits),
        "themes": parse_json_like(story.themes),
    }
