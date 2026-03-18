import re

from backend.continuity.continuity_repository import (
    CharacterRecord,
    CharacterRelationshipRecord,
    StoryEventRecord,
    WorldRuleRecord,
)


CONTRADICTION_PAIRS = [
    ("befriend", "attack"),
    ("befriended", "attacked"),
    ("friend", "enemy"),
    ("friends", "enemies"),
    ("saved", "destroyed"),
    ("protected", "destroyed"),
    ("rebuilt", "destroyed"),
    ("healed", "hurt"),
    ("peace", "war"),
    ("peaceful", "battle"),
    ("found", "lost"),
]

NEGATION_TERMS = {"no", "not", "never", "cannot", "can't", "without"}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
    "world",
    "story",
}
FRIENDLY_RELATIONSHIPS = {"friend", "friends", "ally", "allies", "family", "mentor", "helper"}
HOSTILE_RELATIONSHIPS = {"enemy", "enemies", "rival", "rivals", "foe", "opponent"}
HOSTILE_ACTIONS = {"attack", "attacked", "betray", "betrayed", "fight", "fought", "enemy", "enemies"}
COOPERATIVE_ACTIONS = {"help", "helped", "save", "saved", "befriend", "befriended", "ally", "allies"}
TRAIT_CONTRADICTIONS = {
    "brave": {"cowardly", "afraid"},
    "kind": {"cruel", "mean"},
    "helpful": {"selfish"},
    "honest": {"dishonest", "lying"},
    "patient": {"reckless", "impatient"},
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z']+", _normalize_text(value))
        if token not in STOP_WORDS
    }


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _has_negation(text: str) -> bool:
    return any(_contains_term(text, term) for term in NEGATION_TERMS)


def detect_story_conflicts(
    story_summary: str,
    story_events: list[StoryEventRecord],
    world_events: list[StoryEventRecord],
) -> list[str]:
    normalized_summary = _normalize_text(story_summary)
    summary_tokens = _tokenize(story_summary)
    conflicts: list[str] = []
    seen: set[str] = set()

    for event in story_events + world_events:
        if not event.event_summary:
            continue

        event_text = _normalize_text(event.event_summary)
        event_tokens = _tokenize(event.event_summary)
        overlap = summary_tokens.intersection(event_tokens)

        if overlap:
            for positive, negative in CONTRADICTION_PAIRS:
                if _contains_term(event_text, positive) and _contains_term(normalized_summary, negative):
                    message = (
                        f"Proposed story conflicts with historical event '{event.event_summary}'"
                    )
                    if message not in seen:
                        conflicts.append(message)
                        seen.add(message)
                if _contains_term(event_text, negative) and _contains_term(normalized_summary, positive):
                    message = (
                        f"Proposed story conflicts with historical event '{event.event_summary}'"
                    )
                    if message not in seen:
                        conflicts.append(message)
                        seen.add(message)

        if _has_negation(normalized_summary) and overlap and len(overlap) >= 2:
            message = f"Proposed story may negate established event '{event.event_summary}'"
            if message not in seen:
                conflicts.append(message)
                seen.add(message)

    return conflicts


def detect_character_conflicts(
    story_summary: str,
    character: CharacterRecord,
    events: list[StoryEventRecord],
    relationships: list[CharacterRelationshipRecord],
) -> list[str]:
    normalized_summary = _normalize_text(story_summary)
    conflicts = detect_story_conflicts(story_summary, events, [])
    seen = set(conflicts)

    if character.name:
        character_name = _normalize_text(character.name)
        mentions_character = character_name in normalized_summary
    else:
        mentions_character = False

    if mentions_character:
        summary_tokens = _tokenize(story_summary)
        for relationship in relationships:
            relation = _normalize_text(relationship.relationship_type or "")
            if relation in FRIENDLY_RELATIONSHIPS and summary_tokens.intersection(HOSTILE_ACTIONS):
                message = (
                    f"Proposed story conflicts with established friendly relationship '{relationship.relationship_type}'"
                )
                if message not in seen:
                    conflicts.append(message)
                    seen.add(message)

            if relation in HOSTILE_RELATIONSHIPS and summary_tokens.intersection(COOPERATIVE_ACTIONS):
                message = (
                    f"Proposed story conflicts with established hostile relationship '{relationship.relationship_type}'"
                )
                if message not in seen:
                    conflicts.append(message)
                    seen.add(message)

        for trait in character.personality_traits:
            normalized_trait = _normalize_text(trait)
            opposite_terms = TRAIT_CONTRADICTIONS.get(normalized_trait)
            if not opposite_terms:
                continue
            for opposite in opposite_terms:
                if _contains_term(normalized_summary, opposite):
                    message = (
                        f"Proposed story conflicts with {character.name}'s established trait '{trait}'"
                    )
                    if message not in seen:
                        conflicts.append(message)
                        seen.add(message)

    return conflicts


def detect_world_conflicts(
    story_summary: str,
    world_events: list[StoryEventRecord],
    world_rules: list[WorldRuleRecord],
    location_names: list[str],
) -> list[str]:
    normalized_summary = _normalize_text(story_summary)
    summary_tokens = _tokenize(story_summary)
    conflicts = detect_story_conflicts(story_summary, [], world_events)
    seen = set(conflicts)

    for rule in world_rules:
        rule_text = " ".join(
            part for part in [rule.rule_type or "", rule.rule_description or ""] if part
        ).strip()
        if not rule_text:
            continue
        rule_tokens = _tokenize(rule_text)
        overlap = summary_tokens.intersection(rule_tokens)
        if overlap and _has_negation(normalized_summary):
            message = f"Proposed story conflicts with world rule '{rule_text}'"
            if message not in seen:
                conflicts.append(message)
                seen.add(message)

    normalized_locations = [location.lower() for location in location_names if location.strip()]
    for event in world_events:
        if not event.event_summary:
            continue
        event_text = _normalize_text(event.event_summary)
        if any(location in event_text for location in normalized_locations):
            for positive, negative in CONTRADICTION_PAIRS:
                if _contains_term(event_text, positive) and _contains_term(normalized_summary, negative):
                    message = (
                        f"Proposed story conflicts with established world state '{event.event_summary}'"
                    )
                    if message not in seen:
                        conflicts.append(message)
                        seen.add(message)
                if _contains_term(event_text, negative) and _contains_term(normalized_summary, positive):
                    message = (
                        f"Proposed story conflicts with established world state '{event.event_summary}'"
                    )
                    if message not in seen:
                        conflicts.append(message)
                        seen.add(message)

    return conflicts
