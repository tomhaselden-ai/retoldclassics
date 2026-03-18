from __future__ import annotations

from typing import Any


FRIENDLY_FIGURE_STEPS = [
    "sun_hat",
    "smile",
    "shirt",
    "shorts",
    "left_shoe",
    "right_shoe",
]

REWARD_PROFILE = {
    "correct_message_pool": [
        "Nice work!",
        "You got it!",
        "Great reading!",
    ],
    "incorrect_message_pool": [
        "Good try. Let's keep going.",
        "Almost there. Try again.",
        "Keep exploring. You've got this.",
    ],
    "completion_message": "Practice complete. Great job reading today.",
}


def _normalize_word_letters(word: str) -> str:
    letters = "".join(character for character in word if character.isalpha())
    return letters or word.replace(" ", "")


def _pick_clue(item: dict[str, Any]) -> str:
    definition = item.get("definition")
    if isinstance(definition, str) and definition.strip():
        return definition.strip()
    example_sentence = item.get("example_sentence")
    if isinstance(example_sentence, str) and example_sentence.strip():
        return example_sentence.strip()
    return f"Find the word: {item['word']}"


def _scramble_letters(word: str) -> list[str]:
    letters = list(_normalize_word_letters(word).upper())
    if len(letters) <= 1:
        return letters

    rotated = letters[1:] + letters[:1]
    if rotated != letters:
        return rotated

    reversed_letters = list(reversed(letters))
    if reversed_letters != letters:
        return reversed_letters

    return letters


def _base_payload(game_type: str, difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "game_type": game_type,
        "difficulty_level": difficulty_level,
        "item_count": len(items),
        "items": items,
        "reward_profile": REWARD_PROFILE,
    }


def _build_the_word_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _base_payload("build_the_word", difficulty_level, items)
    payload["figure_style"] = "friendly_growth_figure"
    payload["max_incorrect_guesses"] = len(FRIENDLY_FIGURE_STEPS)
    payload["figure_steps"] = FRIENDLY_FIGURE_STEPS
    payload["rounds"] = [
        {
            "round_id": f"build-{index + 1}",
            "word_id": item["word_id"],
            "target_word": item["word"],
            "normalized_word": _normalize_word_letters(item["word"]).upper(),
            "clue": _pick_clue(item),
            "example_sentence": item.get("example_sentence"),
            "letter_count": len(_normalize_word_letters(item["word"])),
            "starting_pattern": ["_" for _ in _normalize_word_letters(item["word"])],
        }
        for index, item in enumerate(items)
    ]
    return payload


def _guess_the_word_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _base_payload("guess_the_word", difficulty_level, items)
    payload["rounds"] = [
        {
            "round_id": f"guess-{index + 1}",
            "word_id": item["word_id"],
            "target_word": item["word"],
            "normalized_word": _normalize_word_letters(item["word"]).upper(),
            "clue": _pick_clue(item),
            "letter_boxes": len(_normalize_word_letters(item["word"])),
            "example_sentence": item.get("example_sentence"),
        }
        for index, item in enumerate(items)
    ]
    return payload


def _word_match_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    pair_items = items[:8]
    cards: list[dict[str, Any]] = []
    for index, item in enumerate(pair_items):
        pair_id = f"pair-{index + 1}"
        definition = _pick_clue(item)
        cards.append(
            {
                "card_id": f"{pair_id}-word",
                "pair_id": pair_id,
                "card_type": "word",
                "value": item["word"],
                "word_id": item["word_id"],
            }
        )
        cards.append(
            {
                "card_id": f"{pair_id}-meaning",
                "pair_id": pair_id,
                "card_type": "meaning",
                "value": definition,
                "word_id": item["word_id"],
            }
        )

    payload = _base_payload("word_match", difficulty_level, pair_items)
    payload["grid"] = {
        "columns": 4,
        "rows": max(1, len(cards) // 4),
        "cards": cards,
    }
    return payload


def _word_scramble_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _base_payload("word_scramble", difficulty_level, items)
    payload["rounds"] = [
        {
            "round_id": f"scramble-{index + 1}",
            "word_id": item["word_id"],
            "target_word": item["word"],
            "normalized_word": _normalize_word_letters(item["word"]).upper(),
            "scrambled_letters": _scramble_letters(item["word"]),
            "clue": _pick_clue(item),
        }
        for index, item in enumerate(items)
    ]
    return payload


def _flash_cards_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _base_payload("flash_cards", difficulty_level, items)
    payload["cards"] = [
        {
            "card_id": f"flash-{index + 1}",
            "word_id": item["word_id"],
            "front_text": item["word"],
            "back_text": _pick_clue(item),
            "example_sentence": item.get("example_sentence"),
        }
        for index, item in enumerate(items)
    ]
    return payload


def build_v1_game_payload(*, game_type: str, difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    if game_type == "build_the_word":
        return _build_the_word_payload(difficulty_level, items)
    if game_type == "guess_the_word":
        return _guess_the_word_payload(difficulty_level, items)
    if game_type == "word_match":
        return _word_match_payload(difficulty_level, items)
    if game_type == "word_scramble":
        return _word_scramble_payload(difficulty_level, items)
    if game_type == "flash_cards":
        return _flash_cards_payload(difficulty_level, items)
    raise ValueError(f"Unsupported game type: {game_type}")
