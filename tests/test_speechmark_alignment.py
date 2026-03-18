import unittest

from backend.narration.speechmark_alignment import coerce_speech_marks, normalize_speech_marks_for_text


class SpeechMarkAlignmentTests(unittest.TestCase):
    def test_coerce_speech_marks_parses_json_string_payload(self) -> None:
        raw = '[{"time": 0, "type": "word", "start": 50, "end": 53, "value": "One"}]'

        marks = coerce_speech_marks(raw)

        self.assertEqual(1, len(marks))
        self.assertEqual("One", marks[0]["value"])

    def test_normalize_speech_marks_reanchors_word_offsets_to_visible_text(self) -> None:
        visible_text = "One sunny morning in Dream."
        raw_marks = [
            {"time": 0, "type": "sentence", "start": 50, "end": 77, "value": visible_text},
            {"time": 0, "type": "word", "start": 50, "end": 53, "value": "One"},
            {"time": 700, "type": "word", "start": 54, "end": 59, "value": "sunny"},
            {"time": 1100, "type": "word", "start": 60, "end": 67, "value": "morning"},
            {"time": 1450, "type": "word", "start": 68, "end": 70, "value": "in"},
            {"time": 1600, "type": "word", "start": 71, "end": 76, "value": "Dream"},
        ]

        normalized = normalize_speech_marks_for_text(visible_text, raw_marks)

        word_marks = [mark for mark in normalized if mark.get("type") == "word"]
        self.assertEqual((0, 3), (word_marks[0]["start"], word_marks[0]["end"]))
        self.assertEqual((4, 9), (word_marks[1]["start"], word_marks[1]["end"]))
        self.assertEqual((10, 17), (word_marks[2]["start"], word_marks[2]["end"]))
        self.assertEqual((18, 20), (word_marks[3]["start"], word_marks[3]["end"]))
        self.assertEqual((21, 26), (word_marks[4]["start"], word_marks[4]["end"]))

    def test_normalize_speech_marks_handles_apostrophes(self) -> None:
        visible_text = "Wouldn't it be wonderful?"
        raw_marks = [
            {"time": 0, "type": "word", "start": 40, "end": 48, "value": "Wouldn't"},
            {"time": 600, "type": "word", "start": 49, "end": 51, "value": "it"},
        ]

        normalized = normalize_speech_marks_for_text(visible_text, raw_marks)

        self.assertEqual((0, 8), (normalized[0]["start"], normalized[0]["end"]))
        self.assertEqual((9, 11), (normalized[1]["start"], normalized[1]["end"]))


if __name__ == "__main__":
    unittest.main()
