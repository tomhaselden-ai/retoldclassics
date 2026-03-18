import random
import unittest
from types import SimpleNamespace

from backend.games.game_generator import (
    build_character_memory_questions,
    build_story_comprehension_questions,
    build_vocabulary_quiz_questions,
    build_word_puzzle_questions,
)


class GameGeneratorTests(unittest.TestCase):
    def test_word_puzzle_questions_include_answer(self) -> None:
        questions = build_word_puzzle_questions(
            [
                SimpleNamespace(word="Lantern"),
                SimpleNamespace(word="Garden"),
                SimpleNamespace(word="Forest"),
            ],
            2,
            random.Random(7),
        )

        self.assertTrue(all("answer" in question for question in questions))
        self.assertTrue(all(question["answer"] in question["choices"] for question in questions))

    def test_vocabulary_quiz_questions_include_answer(self) -> None:
        questions = build_vocabulary_quiz_questions(
            [
                SimpleNamespace(word="Wonder", difficulty_level=1),
                SimpleNamespace(word="Morning", difficulty_level=1),
            ],
            ["Lantern", "Garden", "Forest", "Curious"],
            2,
            random.Random(11),
        )

        self.assertTrue(all("answer" in question for question in questions))
        self.assertTrue(all(question["answer"] in question["choices"] for question in questions))

    def test_story_comprehension_questions_include_answer(self) -> None:
        questions = build_story_comprehension_questions(
            "The Story",
            [
                SimpleNamespace(event_summary="The lantern glowed.", location_name="Plaza"),
                SimpleNamespace(event_summary="The bird sang.", location_name="Garden"),
            ],
            ["The moon slept.", "The fox hid.", "The river shone."],
            2,
            random.Random(13),
        )

        self.assertTrue(all("answer" in question for question in questions))
        self.assertTrue(all(question["answer"] in question["choices"] for question in questions))

    def test_character_memory_questions_include_answer(self) -> None:
        questions = build_character_memory_questions(
            "The Story",
            [
                SimpleNamespace(event_summary="Olly found the map.", characters=[1, 2]),
                SimpleNamespace(event_summary="Tweet opened the gate.", characters=[2]),
            ],
            {1: "Olly", 2: "Tweet"},
            ["Ari", "Lum", "Pip"],
            2,
            random.Random(17),
        )

        self.assertTrue(all("answer" in question for question in questions))
        self.assertTrue(all(question["answer"] in question["choices"] for question in questions))


if __name__ == "__main__":
    unittest.main()
