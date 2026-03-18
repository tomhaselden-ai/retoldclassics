from __future__ import annotations

from collections import defaultdict
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


def _crossword_layout(items: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [
        {
            "entry_id": f"entry-{index + 1}",
            "word_id": item["word_id"],
            "answer": _normalize_word_letters(item["word"]).upper(),
            "display_word": item["word"],
            "clue": _pick_clue(item),
            "example_sentence": item.get("example_sentence"),
        }
        for index, item in enumerate(items)
        if _normalize_word_letters(item["word"])
    ]

    if not entries:
        return {"rows": 0, "columns": 0, "cells": [], "entries": []}

    entries.sort(key=lambda entry: (-len(entry["answer"]), entry["answer"]))
    placements: list[dict[str, Any]] = [
        {
            **entries[0],
            "direction": "across",
            "row": 0,
            "column": 0,
        }
    ]

    occupied: dict[tuple[int, int], str] = {
        (0, index): letter
        for index, letter in enumerate(entries[0]["answer"])
    }

    def can_place(answer: str, row: int, column: int, direction: str) -> bool:
        for index, letter in enumerate(answer):
            current_row = row + index if direction == "down" else row
            current_column = column + index if direction == "across" else column
            existing = occupied.get((current_row, current_column))
            if existing is not None and existing != letter:
                return False
        return True

    def place_entry(entry: dict[str, Any], row: int, column: int, direction: str) -> None:
        placements.append(
            {
                **entry,
                "direction": direction,
                "row": row,
                "column": column,
            }
        )
        for index, letter in enumerate(entry["answer"]):
            current_row = row + index if direction == "down" else row
            current_column = column + index if direction == "across" else column
            occupied[(current_row, current_column)] = letter

    for entry in entries[1:]:
        placed = False
        for existing in placements:
            for existing_index, existing_letter in enumerate(existing["answer"]):
                if placed:
                    break
                for answer_index, answer_letter in enumerate(entry["answer"]):
                    if answer_letter != existing_letter:
                        continue
                    direction = "down" if existing["direction"] == "across" else "across"
                    row = existing["row"] + existing_index if existing["direction"] == "down" else existing["row"] - answer_index
                    column = existing["column"] - answer_index if existing["direction"] == "across" else existing["column"] + existing_index
                    if can_place(entry["answer"], row, column, direction):
                        place_entry(entry, row, column, direction)
                        placed = True
                        break
        if not placed:
            fallback_row = max(placement["row"] for placement in placements) + 2
            place_entry(entry, fallback_row, 0, "across")

    min_row = min(placement["row"] for placement in placements)
    min_column = min(placement["column"] for placement in placements)

    normalized_placements = []
    for placement in placements:
        normalized_placements.append(
            {
                **placement,
                "row": placement["row"] - min_row,
                "column": placement["column"] - min_column,
            }
        )

    cell_lookup: dict[tuple[int, int], dict[str, Any]] = {}
    clue_number = 1
    clue_numbers: dict[tuple[int, int], int] = {}

    for placement in sorted(normalized_placements, key=lambda item: (item["row"], item["column"], item["direction"])):
        start = (placement["row"], placement["column"])
        if start not in clue_numbers:
            clue_numbers[start] = clue_number
            clue_number += 1
        placement["clue_number"] = clue_numbers[start]
        for index, letter in enumerate(placement["answer"]):
            row = placement["row"] + index if placement["direction"] == "down" else placement["row"]
            column = placement["column"] + index if placement["direction"] == "across" else placement["column"]
            cell = cell_lookup.setdefault(
                (row, column),
                {
                    "row": row,
                    "column": column,
                    "solution": letter,
                    "clue_number": clue_numbers[start] if index == 0 else None,
                    "across_entry_id": None,
                    "down_entry_id": None,
                },
            )
            if placement["direction"] == "across":
                cell["across_entry_id"] = placement["entry_id"]
            else:
                cell["down_entry_id"] = placement["entry_id"]

    rows = max((cell["row"] for cell in cell_lookup.values()), default=-1) + 1
    columns = max((cell["column"] for cell in cell_lookup.values()), default=-1) + 1

    return {
        "rows": rows,
        "columns": columns,
        "cells": sorted(cell_lookup.values(), key=lambda cell: (cell["row"], cell["column"])),
        "entries": sorted(
            [
                {
                    "entry_id": placement["entry_id"],
                    "word_id": placement["word_id"],
                    "display_word": placement["display_word"],
                    "answer": placement["answer"],
                    "clue": placement["clue"],
                    "example_sentence": placement["example_sentence"],
                    "direction": placement["direction"],
                    "row": placement["row"],
                    "column": placement["column"],
                    "clue_number": placement["clue_number"],
                    "length": len(placement["answer"]),
                }
                for placement in normalized_placements
            ],
            key=lambda entry: (entry["clue_number"], entry["direction"]),
        ),
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


def _crossword_payload(difficulty_level: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _base_payload("crossword", difficulty_level, items[:6])
    crossword = _crossword_layout(items[:6])
    entries = crossword["entries"]
    by_direction: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_direction[entry["direction"]].append(entry)
    payload["crossword"] = {
        "rows": crossword["rows"],
        "columns": crossword["columns"],
        "cells": crossword["cells"],
        "entries": entries,
        "across_clues": by_direction["across"],
        "down_clues": by_direction["down"],
    }
    return payload


def build_v1_game_payload(
    *,
    game_type: str,
    difficulty_level: int,
    items: list[dict[str, Any]],
    launch_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if game_type == "build_the_word":
        payload = _build_the_word_payload(difficulty_level, items)
    elif game_type == "guess_the_word":
        payload = _guess_the_word_payload(difficulty_level, items)
    elif game_type == "word_match":
        payload = _word_match_payload(difficulty_level, items)
    elif game_type == "word_scramble":
        payload = _word_scramble_payload(difficulty_level, items)
    elif game_type == "flash_cards":
        payload = _flash_cards_payload(difficulty_level, items)
    elif game_type == "crossword":
        payload = _crossword_payload(difficulty_level, items)
    else:
        raise ValueError(f"Unsupported game type: {game_type}")
    if launch_config:
        payload["launch_config"] = launch_config
    return payload
