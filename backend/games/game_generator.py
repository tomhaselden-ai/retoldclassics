import random
from typing import Any

from backend.games.game_repository import StoryEventRecord, VocabularyRecord


class GameGenerationError(Exception):
    pass


def _dedupe_words(words: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for word in words:
        normalized = word.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _dedupe_summaries(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _build_choice_list(correct: str, distractors: list[str], rng: random.Random) -> list[str]:
    unique_distractors = [item for item in _dedupe_words(distractors) if item.lower() != correct.lower()]
    choices = [correct] + unique_distractors[:3]
    if len(choices) < 2:
        raise GameGenerationError("missing_choices")
    rng.shuffle(choices)
    return choices


def _scramble_word(word: str, rng: random.Random) -> str:
    letters = list(word)
    if len(letters) <= 1:
        return word

    for _ in range(6):
        rng.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled.lower() != word.lower():
            return scrambled
    return word[::-1]


def build_word_puzzle_questions(
    vocabulary_items: list[VocabularyRecord],
    question_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    valid_items = [item for item in vocabulary_items if item.word and len(item.word.strip()) >= 3]
    if len(valid_items) < 2:
        raise GameGenerationError("insufficient_word_data")

    questions: list[dict[str, Any]] = []
    for index, item in enumerate(valid_items[:question_count], start=1):
        target = item.word.strip()
        distractors = [
            candidate.word.strip()
            for candidate in valid_items
            if candidate.word and candidate.word.strip().lower() != target.lower()
        ]
        choices = _build_choice_list(target, distractors, rng)
        questions.append(
            {
                "question_id": f"word-puzzle-{index}",
                "prompt": "Unscramble the story word.",
                "context_text": _scramble_word(target, rng),
                "choices": choices,
                "answer": target,
            }
        )
    return questions


def build_vocabulary_quiz_questions(
    vocabulary_items: list[VocabularyRecord],
    distractor_words: list[str],
    question_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    valid_items = [item for item in vocabulary_items if item.word]
    if not valid_items:
        raise GameGenerationError("insufficient_vocabulary_data")

    questions: list[dict[str, Any]] = []
    for index, item in enumerate(valid_items[:question_count], start=1):
        target = item.word.strip()
        choices = _build_choice_list(target, distractor_words, rng)
        questions.append(
            {
                "question_id": f"vocabulary-quiz-{index}",
                "prompt": "Which of these words appeared in your recent stories?",
                "context_text": f"Difficulty level {item.difficulty_level or 1}",
                "choices": choices,
                "answer": target,
            }
        )
    return questions


def build_story_comprehension_questions(
    story_title: str | None,
    story_events: list[StoryEventRecord],
    distractor_events: list[str],
    question_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    valid_events = [event for event in story_events if event.event_summary]
    if not valid_events:
        raise GameGenerationError("insufficient_story_events")

    deduped_distractors = _dedupe_summaries(distractor_events)
    questions: list[dict[str, Any]] = []
    for index, event in enumerate(valid_events[:question_count], start=1):
        correct = event.event_summary.strip()
        choices = _build_choice_list(correct, deduped_distractors, rng)
        prompt = "Which event happened in this story?"
        if story_title:
            prompt = f"Which event happened in \"{story_title}\"?"
        questions.append(
            {
                "question_id": f"story-comprehension-{index}",
                "prompt": prompt,
                "context_text": event.location_name,
                "choices": choices,
                "answer": correct,
            }
        )
    return questions


def build_character_memory_questions(
    story_title: str | None,
    story_events: list[StoryEventRecord],
    character_name_lookup: dict[int, str],
    distractor_names: list[str],
    question_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    valid_events = [
        event
        for event in story_events
        if event.event_summary and any(character_id in character_name_lookup for character_id in event.characters)
    ]
    if not valid_events:
        raise GameGenerationError("insufficient_character_memory_data")

    questions: list[dict[str, Any]] = []
    for index, event in enumerate(valid_events[:question_count], start=1):
        available_character_ids = [character_id for character_id in event.characters if character_id in character_name_lookup]
        target_id = available_character_ids[0]
        target_name = character_name_lookup[target_id]
        choices = _build_choice_list(target_name, distractor_names, rng)
        prompt = "Which character was involved in this story event?"
        if story_title:
            prompt = f"Which character was involved in this event from \"{story_title}\"?"
        questions.append(
            {
                "question_id": f"character-memory-{index}",
                "prompt": prompt,
                "context_text": event.event_summary,
                "choices": choices,
                "answer": target_name,
            }
        )
    return questions
