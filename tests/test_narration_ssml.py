import unittest

from backend.narration.pronunciation import PronunciationRule
from backend.narration.ssml_builder import build_storytelling_ssml
from backend.narration.text_preprocessor import build_narration_document


FIXTURES = {
    "calm": "The lantern glowed softly in the quiet room. Mira sat by the window and listened to the rain.",
    "dialogue": '"Do you hear that?" Leo whispered. "I think someone is outside." Mara held her breath and listened.',
    "suspense": "At that moment, the floorboards creaked... and the hidden door began to open.",
    "moral": "From that day on, they remembered that kindness shared in small moments can brighten the whole world.",
    "fantasy_names": "Ari carried the Moonlace Compass through Eldervale while Luma watched the silver gate.",
}


class NarrationSsmlTests(unittest.TestCase):
    def test_ssml_is_deterministic(self) -> None:
        document = build_narration_document(FIXTURES["calm"], "classic_read_aloud")
        first = build_storytelling_ssml(document)
        second = build_storytelling_ssml(document)
        self.assertEqual(first, second)

    def test_unsupported_pitch_and_emphasis_are_not_emitted(self) -> None:
        document = build_narration_document(FIXTURES["suspense"], "dramatic_intro")
        ssml = build_storytelling_ssml(document)
        self.assertNotIn("<emphasis", ssml)
        self.assertNotIn("pitch=", ssml)

    def test_dialogue_and_moral_produce_sentence_wrapping(self) -> None:
        dialogue_document = build_narration_document(FIXTURES["dialogue"], "playful_adventure")
        moral_document = build_narration_document(FIXTURES["moral"], "bedtime")
        dialogue_ssml = build_storytelling_ssml(dialogue_document)
        moral_ssml = build_storytelling_ssml(moral_document)
        self.assertIn("<speak>", dialogue_ssml)
        self.assertIn("<p>", dialogue_ssml)
        self.assertIn("<s>", dialogue_ssml)
        self.assertIn("<speak>", moral_ssml)
        self.assertIn("<prosody", moral_ssml)

    def test_pronunciation_overrides_use_supported_ssml(self) -> None:
        document = build_narration_document(FIXTURES["fantasy_names"], "classic_read_aloud")
        ssml = build_storytelling_ssml(
            document,
            pronunciation_rules={
                "Ari": PronunciationRule(alias="Ah-ree"),
                "Eldervale": PronunciationRule(alias="EL-der-vayl"),
            },
        )
        self.assertIn('<sub alias="Ah-ree">Ari</sub>', ssml)
        self.assertIn('<sub alias="EL-der-vayl">Eldervale</sub>', ssml)


if __name__ == "__main__":
    unittest.main()
