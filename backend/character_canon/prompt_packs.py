from __future__ import annotations

from typing import Any


CANON_LIST_FIELDS = {
    "dominant_traits",
    "secondary_traits",
    "core_motivations",
    "fears_and_vulnerabilities",
    "moral_tendencies",
    "behavioral_rules_usually",
    "behavioral_rules_never",
    "behavioral_rules_requires_justification",
    "signature_expressions",
    "continuity_anchors",
    "signature_physical_features",
    "color_palette",
    "visual_must_never_change",
    "visual_may_change",
}

CANON_BOOL_FIELDS = {
    "is_major_character",
    "is_locked",
}

CANON_TEXT_FIELDS = {
    "name",
    "role_in_world",
    "species_or_type",
    "age_category",
    "gender_presentation",
    "archetype",
    "one_sentence_essence",
    "full_personality_summary",
    "speech_style",
    "relationship_tendencies",
    "growth_arc_pattern",
    "visual_summary",
    "form_type",
    "anthropomorphic_level",
    "size_and_proportions",
    "silhouette_description",
    "facial_features",
    "eye_description",
    "fur_skin_surface_description",
    "hair_feather_tail_details",
    "clothing_and_accessories",
    "expression_range",
    "movement_pose_tendencies",
    "art_style_constraints",
    "narrative_prompt_pack_short",
    "visual_prompt_pack_short",
    "continuity_lock_pack",
    "source_status",
    "notes",
}


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if "," in stripped:
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return [stripped]
    return []


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _truncate(value: str | None, limit: int = 700) -> str:
    if not value:
        return ""
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _join(values: list[str], separator: str = ", ") -> str:
    cleaned = [value.strip() for value in values if value and value.strip()]
    return separator.join(cleaned)


def build_base_character_canon(
    *,
    character: Any,
    world: Any,
    reader_world_id: int,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = existing or {}
    traits = _normalize_list(getattr(character, "personality_traits", None))
    dominant_traits = _normalize_list(existing.get("dominant_traits")) or traits[:3]
    secondary_traits = _normalize_list(existing.get("secondary_traits")) or traits[3:6]
    world_name = _normalize_text(getattr(world, "name", None))
    character_name = _normalize_text(getattr(character, "name", None)) or "Unnamed character"
    species = _normalize_text(existing.get("species_or_type")) or _normalize_text(getattr(character, "species", None))
    trait_summary = _join(dominant_traits or traits[:2])

    base = {
        "character_id": getattr(character, "character_id"),
        "world_id": getattr(character, "world_id"),
        "reader_world_id": reader_world_id,
        "name": existing.get("name") or character_name,
        "role_in_world": existing.get("role_in_world") or (f"Resident of {world_name}" if world_name else "World resident"),
        "species_or_type": species,
        "age_category": existing.get("age_category"),
        "gender_presentation": existing.get("gender_presentation"),
        "archetype": existing.get("archetype"),
        "one_sentence_essence": existing.get("one_sentence_essence")
        or _truncate(
            f"{character_name} is a recurring {species or 'character'}"
            + (f" from {world_name}" if world_name else "")
            + (f" who is known for being {trait_summary}." if trait_summary else "."),
            220,
        ),
        "full_personality_summary": existing.get("full_personality_summary")
        or _truncate(
            f"{character_name} is typically portrayed as {trait_summary or 'thoughtful and story-ready'}"
            + (f" within the world of {world_name}." if world_name else "."),
            320,
        ),
        "dominant_traits": dominant_traits,
        "secondary_traits": secondary_traits,
        "core_motivations": _normalize_list(existing.get("core_motivations")),
        "fears_and_vulnerabilities": _normalize_list(existing.get("fears_and_vulnerabilities")),
        "moral_tendencies": _normalize_list(existing.get("moral_tendencies")),
        "behavioral_rules_usually": _normalize_list(existing.get("behavioral_rules_usually")),
        "behavioral_rules_never": _normalize_list(existing.get("behavioral_rules_never")),
        "behavioral_rules_requires_justification": _normalize_list(existing.get("behavioral_rules_requires_justification")),
        "speech_style": existing.get("speech_style"),
        "signature_expressions": _normalize_list(existing.get("signature_expressions")),
        "relationship_tendencies": existing.get("relationship_tendencies"),
        "growth_arc_pattern": existing.get("growth_arc_pattern"),
        "continuity_anchors": _normalize_list(existing.get("continuity_anchors")),
        "visual_summary": existing.get("visual_summary")
        or _truncate(
            f"{character_name} is shown as a {species or 'storybook character'}"
            + (f" from {world_name}" if world_name else "")
            + " with a child-friendly, readable silhouette.",
            260,
        ),
        "form_type": existing.get("form_type") or species,
        "anthropomorphic_level": existing.get("anthropomorphic_level"),
        "size_and_proportions": existing.get("size_and_proportions"),
        "silhouette_description": existing.get("silhouette_description"),
        "facial_features": existing.get("facial_features"),
        "eye_description": existing.get("eye_description"),
        "fur_skin_surface_description": existing.get("fur_skin_surface_description"),
        "hair_feather_tail_details": existing.get("hair_feather_tail_details"),
        "clothing_and_accessories": existing.get("clothing_and_accessories"),
        "signature_physical_features": _normalize_list(existing.get("signature_physical_features")),
        "expression_range": existing.get("expression_range"),
        "movement_pose_tendencies": existing.get("movement_pose_tendencies"),
        "color_palette": _normalize_list(existing.get("color_palette")),
        "art_style_constraints": existing.get("art_style_constraints"),
        "visual_must_never_change": _normalize_list(existing.get("visual_must_never_change")),
        "visual_may_change": _normalize_list(existing.get("visual_may_change")),
        "narrative_prompt_pack_short": _normalize_text(existing.get("narrative_prompt_pack_short")),
        "visual_prompt_pack_short": _normalize_text(existing.get("visual_prompt_pack_short")),
        "continuity_lock_pack": _normalize_text(existing.get("continuity_lock_pack")),
        "source_status": _normalize_text(existing.get("source_status")) or "legacy",
        "canon_version": int(existing.get("canon_version") or 1),
        "enhanced_at": existing.get("enhanced_at"),
        "enhanced_by": existing.get("enhanced_by"),
        "last_reviewed_at": existing.get("last_reviewed_at"),
        "is_major_character": _normalize_bool(existing.get("is_major_character")),
        "is_locked": _normalize_bool(existing.get("is_locked")),
        "notes": _normalize_text(existing.get("notes")),
    }
    return base


def merge_character_canon_input(
    base_profile: dict[str, Any],
    updates: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = dict(base_profile)
    updates = updates or {}

    for field in CANON_LIST_FIELDS:
        if field in updates:
            profile[field] = _normalize_list(updates.get(field))

    for field in CANON_TEXT_FIELDS:
        if field in updates:
            profile[field] = _normalize_text(updates.get(field))

    for field in CANON_BOOL_FIELDS:
        if field in updates:
            profile[field] = _normalize_bool(updates.get(field))

    for identifier_field in ("character_id", "world_id", "reader_world_id", "enhanced_by", "canon_version"):
        if identifier_field in updates and updates.get(identifier_field) is not None:
            profile[identifier_field] = updates.get(identifier_field)

    return profile


def build_prompt_packs(profile: dict[str, Any]) -> tuple[str, str, str]:
    essence = _normalize_text(profile.get("one_sentence_essence")) or ""
    personality = _normalize_text(profile.get("full_personality_summary")) or ""
    dominant_traits = _join(_normalize_list(profile.get("dominant_traits")))
    motivations = _join(_normalize_list(profile.get("core_motivations")))
    usually_rules = _join(_normalize_list(profile.get("behavioral_rules_usually")), "; ")
    never_rules = _join(_normalize_list(profile.get("behavioral_rules_never")), "; ")
    speech_style = _normalize_text(profile.get("speech_style")) or ""
    anchors = _join(_normalize_list(profile.get("continuity_anchors")), "; ")

    visual_summary = _normalize_text(profile.get("visual_summary")) or ""
    form_type = _normalize_text(profile.get("form_type")) or ""
    proportions = _normalize_text(profile.get("size_and_proportions")) or ""
    facial_features = _normalize_text(profile.get("facial_features")) or ""
    palette = _join(_normalize_list(profile.get("color_palette")))
    clothing = _normalize_text(profile.get("clothing_and_accessories")) or ""
    features = _join(_normalize_list(profile.get("signature_physical_features")), "; ")
    art_constraints = _normalize_text(profile.get("art_style_constraints")) or ""
    never_change = _join(_normalize_list(profile.get("visual_must_never_change")), "; ")

    narrative_pack = _truncate(
        " ".join(
            part
            for part in [
                essence,
                personality,
                f"Dominant traits: {dominant_traits}." if dominant_traits else "",
                f"Core motivations: {motivations}." if motivations else "",
                f"Usually: {usually_rules}." if usually_rules else "",
                f"Never: {never_rules}." if never_rules else "",
                f"Speech style: {speech_style}." if speech_style else "",
                f"Continuity anchors: {anchors}." if anchors else "",
            ]
            if part
        ),
        700,
    )

    visual_pack = _truncate(
        " ".join(
            part
            for part in [
                visual_summary,
                f"Form: {form_type}." if form_type else "",
                f"Proportions: {proportions}." if proportions else "",
                f"Facial features: {facial_features}." if facial_features else "",
                f"Palette: {palette}." if palette else "",
                f"Clothing/accessories: {clothing}." if clothing else "",
                f"Signature features: {features}." if features else "",
                f"Art constraints: {art_constraints}." if art_constraints else "",
                f"Must never change: {never_change}." if never_change else "",
            ]
            if part
        ),
        700,
    )

    continuity_pack = _truncate(
        " ".join(
            part
            for part in [
                f"Anchors: {anchors}." if anchors else "",
                f"Behavior never: {never_rules}." if never_rules else "",
                f"Behavior usually: {usually_rules}." if usually_rules else "",
                f"Speech style: {speech_style}." if speech_style else "",
                f"Visual locks: {never_change}." if never_change else "",
                f"Palette lock: {palette}." if palette else "",
            ]
            if part
        ),
        700,
    )

    return narrative_pack, visual_pack, continuity_pack


def finalize_character_canon(profile: dict[str, Any]) -> dict[str, Any]:
    finalized = dict(profile)
    narrative_pack, visual_pack, continuity_pack = build_prompt_packs(finalized)
    finalized["narrative_prompt_pack_short"] = narrative_pack
    finalized["visual_prompt_pack_short"] = visual_pack
    finalized["continuity_lock_pack"] = continuity_pack
    return finalized


def build_story_character_guidance(character: Any, canon: dict[str, Any] | None) -> dict[str, Any]:
    if not canon:
        return {
            "character_id": getattr(character, "character_id", None),
            "name": getattr(character, "name", None),
            "species": getattr(character, "species", None),
            "personality_traits": getattr(character, "personality_traits", None),
            "home_location": getattr(character, "home_location", None),
        }

    return {
        "character_id": canon.get("character_id") or getattr(character, "character_id", None),
        "name": canon.get("name") or getattr(character, "name", None),
        "species": canon.get("species_or_type") or getattr(character, "species", None),
        "personality_traits": canon.get("dominant_traits") or getattr(character, "personality_traits", None),
        "home_location": getattr(character, "home_location", None),
        "one_sentence_essence": canon.get("one_sentence_essence"),
        "full_personality_summary": canon.get("full_personality_summary"),
        "dominant_traits": canon.get("dominant_traits"),
        "core_motivations": canon.get("core_motivations"),
        "behavioral_rules_usually": canon.get("behavioral_rules_usually"),
        "behavioral_rules_never": canon.get("behavioral_rules_never"),
        "speech_style": canon.get("speech_style"),
        "continuity_anchors": canon.get("continuity_anchors"),
        "narrative_prompt_pack_short": canon.get("narrative_prompt_pack_short"),
        "source_status": canon.get("source_status"),
        "is_locked": canon.get("is_locked"),
    }


def build_visual_prompt_section(
    character: Any,
    canon: dict[str, Any] | None,
    fallback_style_rules: dict[str, Any] | None = None,
) -> str:
    if canon:
        parts = [
            f"Character: {canon.get('name') or getattr(character, 'name', 'Unknown')}",
            f"Visual summary: {canon.get('visual_summary')}" if canon.get("visual_summary") else "",
            f"Form: {canon.get('form_type')}" if canon.get("form_type") else "",
            f"Proportions: {canon.get('size_and_proportions')}" if canon.get("size_and_proportions") else "",
            f"Facial features: {canon.get('facial_features')}" if canon.get("facial_features") else "",
            f"Eyes: {canon.get('eye_description')}" if canon.get("eye_description") else "",
            f"Surface: {canon.get('fur_skin_surface_description')}" if canon.get("fur_skin_surface_description") else "",
            f"Hair/feathers/tail: {canon.get('hair_feather_tail_details')}" if canon.get("hair_feather_tail_details") else "",
            f"Clothing/accessories: {canon.get('clothing_and_accessories')}" if canon.get("clothing_and_accessories") else "",
            f"Signature features: {_join(_normalize_list(canon.get('signature_physical_features')), '; ')}"
            if _normalize_list(canon.get("signature_physical_features"))
            else "",
            f"Palette: {_join(_normalize_list(canon.get('color_palette')))}"
            if _normalize_list(canon.get("color_palette"))
            else "",
            f"Art constraints: {canon.get('art_style_constraints')}" if canon.get("art_style_constraints") else "",
            f"Must never change: {_join(_normalize_list(canon.get('visual_must_never_change')), '; ')}"
            if _normalize_list(canon.get("visual_must_never_change"))
            else "",
            f"Runtime visual pack: {canon.get('visual_prompt_pack_short')}" if canon.get("visual_prompt_pack_short") else "",
        ]
        return " | ".join(part for part in parts if part)

    fallback_style_rules = fallback_style_rules or {}
    traits = _normalize_list(fallback_style_rules.get("personality_traits"))
    parts = [
        f"Character: {fallback_style_rules.get('character_name') or getattr(character, 'name', 'Unknown')}",
        f"Species: {fallback_style_rules.get('species') or getattr(character, 'species', 'Unknown')}",
        f"Traits: {_join(traits)}" if traits else "",
        f"Home location inspiration: {fallback_style_rules.get('home_location')}"
        if fallback_style_rules.get("home_location")
        else "",
        _normalize_text(fallback_style_rules.get("art_direction")) or "",
    ]
    return " | ".join(part for part in parts if part)
