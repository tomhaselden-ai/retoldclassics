import unittest

from backend.games.v1_game_engine import build_v1_game_payload


def build_items() -> list[dict]:
    return [
        {
            "word_id": 1,
            "word": "Lantern",
            "definition": "A lamp with a handle.",
            "example_sentence": "The lantern glowed at dusk.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": 12,
            "source_type": "story",
            "trait_focus": "curiosity",
        },
        {
            "word_id": 2,
            "word": "Harbor",
            "definition": "A sheltered place for boats.",
            "example_sentence": "The harbor shimmered at dawn.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": 12,
            "source_type": "story",
            "trait_focus": "curiosity",
        },
        {
            "word_id": 3,
            "word": "Meadow",
            "definition": "A grassy field.",
            "example_sentence": None,
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
        {
            "word_id": 4,
            "word": "Pebble",
            "definition": "A small smooth stone.",
            "example_sentence": "A pebble skipped across the pond.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
        {
            "word_id": 5,
            "word": "Canyon",
            "definition": "A deep valley with steep sides.",
            "example_sentence": "The canyon echoed with bird calls.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
        {
            "word_id": 6,
            "word": "Comet",
            "definition": "A bright object that travels through space.",
            "example_sentence": "A comet streaked across the night sky.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
        {
            "word_id": 7,
            "word": "Ripple",
            "definition": "A small wave on water.",
            "example_sentence": "A ripple spread across the pond.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
        {
            "word_id": 8,
            "word": "Willow",
            "definition": "A tree with long hanging branches.",
            "example_sentence": "The willow swayed in the breeze.",
            "difficulty_level": 2,
            "reader_id": 7,
            "story_id": None,
            "source_type": "global_vocab",
            "trait_focus": None,
        },
    ]


class V1GameEngineTests(unittest.TestCase):
    def test_build_the_word_payload_contains_rounds_and_figure_steps(self) -> None:
        payload = build_v1_game_payload(game_type="build_the_word", difficulty_level=2, items=build_items()[:4])

        self.assertEqual(payload["game_type"], "build_the_word")
        self.assertEqual(len(payload["rounds"]), 4)
        self.assertEqual(payload["figure_steps"][0], "sun_hat")
        self.assertEqual(payload["rounds"][0]["normalized_word"], "LANTERN")

    def test_guess_the_word_payload_uses_clues_and_letter_boxes(self) -> None:
        payload = build_v1_game_payload(game_type="guess_the_word", difficulty_level=2, items=build_items()[:4])

        self.assertEqual(payload["game_type"], "guess_the_word")
        self.assertEqual(payload["rounds"][0]["clue"], "A lamp with a handle.")
        self.assertEqual(payload["rounds"][1]["letter_boxes"], 6)

    def test_word_match_payload_builds_word_meaning_pairs(self) -> None:
        payload = build_v1_game_payload(game_type="word_match", difficulty_level=2, items=build_items())

        self.assertEqual(payload["game_type"], "word_match")
        self.assertEqual(payload["grid"]["columns"], 4)
        self.assertEqual(len(payload["grid"]["cards"]), 16)
        self.assertEqual(payload["grid"]["cards"][0]["card_type"], "word")
        self.assertEqual(payload["grid"]["cards"][1]["card_type"], "meaning")

    def test_word_scramble_payload_scrambles_letters(self) -> None:
        payload = build_v1_game_payload(game_type="word_scramble", difficulty_level=2, items=build_items()[:4])

        self.assertEqual(payload["game_type"], "word_scramble")
        self.assertEqual(payload["rounds"][0]["normalized_word"], "LANTERN")
        self.assertNotEqual(payload["rounds"][0]["scrambled_letters"], list("LANTERN"))

    def test_flash_cards_payload_builds_front_and_back(self) -> None:
        payload = build_v1_game_payload(game_type="flash_cards", difficulty_level=2, items=build_items()[:4])

        self.assertEqual(payload["game_type"], "flash_cards")
        self.assertEqual(len(payload["cards"]), 4)
        self.assertEqual(payload["cards"][0]["front_text"], "Lantern")
        self.assertEqual(payload["cards"][0]["back_text"], "A lamp with a handle.")

    def test_crossword_payload_builds_grid_and_clues(self) -> None:
        payload = build_v1_game_payload(game_type="crossword", difficulty_level=2, items=build_items()[:6])

        self.assertEqual(payload["game_type"], "crossword")
        self.assertIn("crossword", payload)
        self.assertGreaterEqual(payload["crossword"]["rows"], 1)
        self.assertGreaterEqual(payload["crossword"]["columns"], 1)
        self.assertGreaterEqual(len(payload["crossword"]["entries"]), 4)
        self.assertGreaterEqual(len(payload["crossword"]["cells"]), 4)
        self.assertTrue(payload["crossword"]["across_clues"] or payload["crossword"]["down_clues"])


if __name__ == "__main__":
    unittest.main()
