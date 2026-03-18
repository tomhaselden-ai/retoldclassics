import unittest

from backend.character_canon.batch_service import (
    _sanitize_relationship_suggestions,
    should_process_character,
)


class CharacterCanonBatchTests(unittest.TestCase):
    def test_sanitize_relationship_suggestions_skips_invalid_and_existing_pairs(self) -> None:
        suggestions = _sanitize_relationship_suggestions(
            [
                {
                    "character_a_name": "Luma",
                    "character_b_name": "Pip",
                    "relationship_type": "friend",
                    "relationship_strength": 8,
                },
                {
                    "character_a_name": "Pip",
                    "character_b_name": "Luma",
                    "relationship_type": "teammate",
                    "relationship_strength": 6,
                },
                {
                    "character_a_name": "Luma",
                    "character_b_name": "Luma",
                    "relationship_type": "friend",
                    "relationship_strength": 4,
                },
                {
                    "character_a_name": "Unknown",
                    "character_b_name": "Pip",
                    "relationship_type": "helper",
                    "relationship_strength": 5,
                },
            ],
            name_to_id={"Luma": 3, "Pip": 5},
            existing_pairs=set(),
        )

        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["character_a_id"], 3)
        self.assertEqual(suggestions[0]["character_b_id"], 5)
        self.assertEqual(suggestions[0]["relationship_type"], "friend")

    def test_sanitize_relationship_suggestions_respects_existing_pairs(self) -> None:
        suggestions = _sanitize_relationship_suggestions(
            [
                {
                    "character_a_name": "Luma",
                    "character_b_name": "Pip",
                    "relationship_type": "friend",
                    "relationship_strength": 8,
                }
            ],
            name_to_id={"Luma": 3, "Pip": 5},
            existing_pairs={(3, 5)},
        )
        self.assertEqual(suggestions, [])

    def test_should_process_character_respects_force_and_locked_status(self) -> None:
        self.assertTrue(should_process_character(None, force=False))
        self.assertFalse(
            should_process_character({"source_status": "canonical", "is_locked": 1}, force=False)
        )
        self.assertTrue(
            should_process_character({"source_status": "canonical", "is_locked": 1}, force=True)
        )
        self.assertTrue(
            should_process_character({"source_status": "enhanced", "is_locked": 0}, force=False)
        )


if __name__ == "__main__":
    unittest.main()
