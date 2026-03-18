import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.character_canon.enhancement_service import generate_character_canon_preview
from backend.character_canon.prompt_packs import (
    build_visual_prompt_section,
    finalize_character_canon,
)
from backend.continuity.continuity_service import _append_character_canon_conflicts
from backend.story_engine.prompt_builder import build_story_prompt


class CharacterCanonPromptTests(unittest.TestCase):
    def test_finalize_character_canon_builds_runtime_prompt_packs(self) -> None:
        profile = finalize_character_canon(
            {
                "name": "Luma",
                "one_sentence_essence": "Luma is a brave owl guide.",
                "full_personality_summary": "Luma is brave, gentle, and observant.",
                "dominant_traits": ["brave", "gentle"],
                "core_motivations": ["protect the forest", "guide younger friends"],
                "behavioral_rules_usually": ["speaks calmly", "helps when someone is lost"],
                "behavioral_rules_never": ["mocks frightened friends"],
                "speech_style": "Warm, patient, short encouraging phrases.",
                "continuity_anchors": ["Always carries a lantern", "Acts as a night guide"],
                "visual_summary": "A moonlit owl with a small travel lantern.",
                "form_type": "owl",
                "size_and_proportions": "Small and rounded with wide wings.",
                "facial_features": "Soft beak and rounded cheeks.",
                "color_palette": ["cream", "gold", "midnight blue"],
                "clothing_and_accessories": "Travel satchel and lantern strap.",
                "signature_physical_features": ["crescent feather mark", "glowing lantern"],
                "art_style_constraints": "storybook watercolor softness",
                "visual_must_never_change": ["crescent feather mark", "gold lantern glow"],
            }
        )

        self.assertIn("Luma is a brave owl guide.", profile["narrative_prompt_pack_short"])
        self.assertIn("gold lantern glow", profile["visual_prompt_pack_short"])
        self.assertIn("Acts as a night guide", profile["continuity_lock_pack"])

    def test_build_story_prompt_includes_character_canon_guidance(self) -> None:
        reader = SimpleNamespace(reader_id=2, age=8, reading_level="2", trait_focus=["kindness"])
        reader_world = SimpleNamespace(reader_world_id=9, world_id=4, custom_name="Moon Meadow")
        character = SimpleNamespace(
            character_id=7,
            name="Luma",
            species="owl",
            personality_traits=["kind", "brave"],
            home_location=3,
        )
        world = SimpleNamespace(world_id=4, name="Moon Meadow", description="A gentle moonlit world.")
        messages = build_story_prompt(
            reader_profile=reader,
            reader_world=reader_world,
            world_context={
                "world": world,
                "characters": [character],
                "locations": [],
                "relationships": [],
            },
            classical_chunks=[],
            theme="courage",
            target_length="short",
            character_canon_lookup={
                7: {
                    "character_id": 7,
                    "name": "Luma",
                    "species_or_type": "owl guide",
                    "one_sentence_essence": "Luma is a calm night guide.",
                    "full_personality_summary": "Luma guides others with calm courage.",
                    "dominant_traits": ["calm", "brave"],
                    "core_motivations": ["protect younger friends"],
                    "behavioral_rules_usually": ["speaks softly"],
                    "behavioral_rules_never": ["leaves frightened friends behind"],
                    "speech_style": "Soft, steady, encouraging.",
                    "continuity_anchors": ["carries a lantern"],
                    "narrative_prompt_pack_short": "Luma is a calm night guide with a lantern.",
                    "source_status": "canonical",
                    "is_locked": True,
                }
            },
        )

        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["characters"][0]["one_sentence_essence"], "Luma is a calm night guide.")
        self.assertEqual(payload["characters"][0]["speech_style"], "Soft, steady, encouraging.")
        self.assertEqual(payload["characters"][0]["behavioral_rules_never"], ["leaves frightened friends behind"])

    def test_build_visual_prompt_section_prefers_visual_canon(self) -> None:
        character = SimpleNamespace(name="Milo", species="fox")
        section = build_visual_prompt_section(
            character,
            {
                "name": "Milo",
                "visual_summary": "A bright red fox with a teal satchel.",
                "form_type": "fox",
                "size_and_proportions": "Small, nimble, oversized tail.",
                "facial_features": "Pointed smile and round eyes.",
                "signature_physical_features": ["white tail tip"],
                "color_palette": ["red", "cream", "teal"],
                "visual_must_never_change": ["white tail tip", "teal satchel"],
            },
        )
        self.assertIn("teal satchel", section)
        self.assertIn("white tail tip", section)

    def test_character_canon_continuity_adds_behavior_and_anchor_conflicts(self) -> None:
        conflicts = _append_character_canon_conflicts(
            "Luma never guides anyone and her lantern is missing.",
            {
                "speech_style": "She speaks warmly and often reassures friends.",
                "behavioral_rules_never": ["never abandons lost children"],
                "continuity_anchors": ["guides lost children through the dark woods"],
                "visual_must_never_change": ["lantern glow"],
            },
            [],
        )
        self.assertGreaterEqual(len(conflicts), 2)


class CharacterCanonEnhancementTests(unittest.TestCase):
    def test_generate_character_canon_preview_uses_account_scoped_world_context(self) -> None:
        db = object()
        world_context = {
            "reader_world": SimpleNamespace(reader_world_id=91),
            "world": SimpleNamespace(world_id=5, name="Dream Harbor", description="A world of floating lights."),
            "characters": [
                SimpleNamespace(
                    character_id=13,
                    world_id=5,
                    name="Pip",
                    species="otter",
                    personality_traits=["curious", "gentle"],
                    home_location=4,
                )
            ],
            "relationships": [],
            "world_rules": [],
            "locations": [],
        }
        with patch(
            "backend.character_canon.enhancement_service.get_reader_world_context_for_account",
            return_value=world_context,
        ) as context_mocked, patch(
            "backend.character_canon.enhancement_service.get_character_canon_profile",
            return_value=None,
        ), patch(
            "backend.character_canon.enhancement_service._scoped_story_events_for_character",
            return_value=[],
        ), patch(
            "backend.character_canon.enhancement_service._call_openai_character_enhancement",
            return_value={
                "narrative": {"speech_style": "Playful and kind."},
                "visual": {"visual_summary": "A warm brown otter with a sea-blue scarf."},
                "metadata": {"is_major_character": True},
            },
        ), patch(
            "backend.character_canon.enhancement_service.insert_character_canon_enhancement_run",
            return_value={"enhancement_run_id": 5},
        ) as insert_mocked:
            payload = generate_character_canon_preview(
                db,
                account_id=42,
                reader_id=2,
                world_id=5,
                character_id=13,
                section_mode="full",
                existing_canon=None,
            )

        context_mocked.assert_called_once_with(db, 42, 2, 5)
        insert_mocked.assert_called_once()
        self.assertEqual(payload["enhancement_run"]["enhancement_run_id"], 5)
        self.assertEqual(payload["preview_profile"]["reader_world_id"], 91)
        self.assertEqual(payload["preview_profile"]["source_status"], "enhanced")


if __name__ == "__main__":
    unittest.main()
