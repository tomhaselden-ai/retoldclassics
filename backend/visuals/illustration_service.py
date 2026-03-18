import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.character_canon.prompt_packs import build_visual_prompt_section
from backend.character_canon.repository import list_character_canon_profiles
from backend.visuals.illustration_repository import (
    build_scene_prompt_seed,
    get_character_visual_profile,
    get_location_for_character,
    get_story_for_account,
    get_story_illustration,
    get_story_scenes,
    get_story_world,
    list_scene_referenced_characters,
    list_story_illustrations,
    list_story_world_characters,
    insert_scene_version_snapshot,
    update_scene_illustration_url,
    upsert_character_visual_profile,
    upsert_scene_illustration,
)
from backend.visuals.image_storage import IllustrationImageStorage
from backend.visuals.openai_image_client import IMAGE_MODEL, OpenAIImageClient


logger = logging.getLogger(__name__)


class IllustrationService:
    def __init__(
        self,
        image_client: OpenAIImageClient | None = None,
        image_storage: IllustrationImageStorage | None = None,
    ) -> None:
        self._image_client = image_client
        self._image_storage = image_storage or IllustrationImageStorage()

    def _build_style_rules(
        self,
        character,
        location,
        world_name: str | None,
    ) -> dict[str, Any]:
        traits = character.personality_traits
        if isinstance(traits, list):
            personality = [str(item).strip() for item in traits if str(item).strip()]
        elif isinstance(traits, str) and traits.strip():
            personality = [traits.strip()]
        else:
            personality = []

        return {
            "character_name": character.name,
            "species": character.species,
            "personality_traits": personality,
            "home_location": location.name if location is not None else None,
            "world_name": world_name,
            "art_direction": "consistent children's storybook design with stable facial features, colors, and clothing/accessories",
        }

    def _merge_reference_images(self, existing_profile, image_url: str) -> list[str]:
        reference_images: list[str] = []
        if existing_profile is not None and isinstance(existing_profile.reference_images, list):
            reference_images = [str(item) for item in existing_profile.reference_images if str(item).strip()]
        if image_url not in reference_images:
            reference_images.append(image_url)
        return reference_images[-5:]

    def _build_scene_prompt(
        self,
        story_title: str | None,
        world_name: str | None,
        scene_order: int | None,
        prompt_seed: dict[str, Any],
        character_sections: list[str],
    ) -> str:
        prompt_parts = [
            "Children's storybook illustration.",
            f"Story title: {story_title or 'Untitled Story'}",
            f"World: {world_name or 'Unknown World'}",
            f"Scene order: {scene_order or 1}",
            "Maintain consistency with previously illustrated scenes. Keep characters visually stable across images.",
        ]

        if prompt_seed.get("illustration_prompt"):
            prompt_parts.append(f"Scene illustration brief: {prompt_seed['illustration_prompt']}")

        paragraphs = prompt_seed.get("paragraphs") or []
        if paragraphs:
            prompt_parts.append(f"Scene text cues: {' '.join(paragraphs[:2])}")
        elif prompt_seed.get("scene_text"):
            prompt_parts.append(f"Scene text cues: {prompt_seed['scene_text']}")

        if character_sections:
            prompt_parts.append("Character consistency rules:")
            prompt_parts.extend(character_sections)

        prompt_parts.append(
            "Style: whimsical children's book illustration, bright colors, soft lighting, storybook composition."
        )
        return "\n\n".join(prompt_parts)

    def story_has_illustration(self, db: Session, account_id: int, story_id: int) -> bool:
        get_story_for_account(db, story_id, account_id)
        illustration = get_story_illustration(db, story_id)
        return bool(illustration is not None and illustration.image_url)

    def get_story_illustration_summary(self, db: Session, account_id: int, story_id: int) -> dict[str, str | int]:
        payload = self.get_story_illustration(db, account_id, story_id)
        return {
            "story_id": story_id,
            "image_url": payload["image_url"],
            "scenes_illustrated": 1,
        }

    def generate_story_illustration(self, db: Session, account_id: int, story_id: int) -> dict[str, str | int]:
        story = get_story_for_account(db, story_id, account_id)
        existing_illustration = get_story_illustration(db, story.story_id)
        if existing_illustration is not None and existing_illustration.image_url:
            normalized_url = self._image_storage.normalize_public_url(existing_illustration.image_url) or existing_illustration.image_url
            return {
                "story_id": story.story_id,
                "image_url": normalized_url,
                "scenes_illustrated": 0,
            }

        scenes = get_story_scenes(db, story.story_id)
        world_row = get_story_world(db, story)
        world_name = getattr(world_row, "name", None)
        story_characters = list_story_world_characters(db, story)
        canon_lookup = list_character_canon_profiles(
            db,
            account_id=account_id,
            reader_world_id=story.reader_world_id,
            character_ids=[
                character.character_id
                for character in story_characters
                if isinstance(getattr(character, "character_id", None), int)
            ],
        )

        logger.info("Generating consistent illustrations for story %s", story.story_id)

        first_image_url: str | None = None
        scenes_illustrated = 0

        try:
            scene = scenes[0]
            prompt_seed = build_scene_prompt_seed(scene)
            referenced_characters = list_scene_referenced_characters(db, scene, story_characters)

            character_sections: list[str] = []
            for character in referenced_characters:
                existing_profile = get_character_visual_profile(db, character.character_id)
                location = get_location_for_character(db, character.home_location)
                style_rules = self._build_style_rules(character, location, world_name)
                canon = canon_lookup.get(character.character_id)

                if existing_profile is not None and isinstance(existing_profile.style_rules, dict):
                    merged_style_rules = dict(existing_profile.style_rules)
                    merged_style_rules.update({key: value for key, value in style_rules.items() if value is not None})
                    style_rules = merged_style_rules

                traits = style_rules.get("personality_traits") or []
                if isinstance(traits, list):
                    traits_text = ", ".join(str(item) for item in traits if str(item).strip())
                else:
                    traits_text = str(traits).strip()

                section_parts = [
                    f"Character: {style_rules.get('character_name') or character.name or 'Unknown'}",
                    f"Species: {style_rules.get('species') or character.species or 'Unknown'}",
                ]
                if traits_text:
                    section_parts.append(f"Traits: {traits_text}")
                if style_rules.get("home_location"):
                    section_parts.append(f"Home location inspiration: {style_rules['home_location']}")
                section_parts.append(style_rules["art_direction"])
                canon_section = build_visual_prompt_section(character, canon, style_rules)
                if canon_section:
                    section_parts.append(canon_section)
                character_sections.append(" | ".join(section_parts))

            final_prompt = self._build_scene_prompt(
                story.title,
                world_name,
                scene.scene_order,
                prompt_seed,
                character_sections,
            )

            image_client = self._image_client or OpenAIImageClient()
            image_bytes = image_client.generate_image(final_prompt)
            image_path = self._image_storage.save_scene_illustration(story.story_id, scene.scene_id, image_bytes)

            illustration = upsert_scene_illustration(
                db=db,
                scene_id=scene.scene_id,
                image_url=image_path,
                prompt_used=final_prompt,
                generation_model=IMAGE_MODEL,
            )
            updated_scene = update_scene_illustration_url(db, scene.scene_id, illustration.image_url or image_path)
            insert_scene_version_snapshot(db, updated_scene)

            for character in referenced_characters:
                existing_profile = get_character_visual_profile(db, character.character_id)
                location = get_location_for_character(db, character.home_location)
                style_rules = self._build_style_rules(character, location, world_name)
                if existing_profile is not None and isinstance(existing_profile.style_rules, dict):
                    merged_style_rules = dict(existing_profile.style_rules)
                    merged_style_rules.update({key: value for key, value in style_rules.items() if value is not None})
                    style_rules = merged_style_rules

                reference_images = self._merge_reference_images(existing_profile, image_path)
                upsert_character_visual_profile(
                    db=db,
                    character_id=character.character_id,
                    reference_images=reference_images,
                    style_rules=style_rules,
                )

            if first_image_url is None:
                first_image_url = illustration.image_url or image_path
            scenes_illustrated = 1

            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.exception("Illustration consistency generation failed", extra={"story_id": story.story_id})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Illustration consistency generation failed",
            ) from exc

        if first_image_url is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scene illustrations could be generated",
            )

        logger.info("Consistent illustration generation complete", extra={"story_id": story.story_id})
        return {
            "story_id": story.story_id,
            "image_url": self._image_storage.normalize_public_url(first_image_url) or first_image_url,
            "scenes_illustrated": scenes_illustrated,
        }

    def get_story_illustration(self, db: Session, account_id: int, story_id: int) -> dict[str, str]:
        get_story_for_account(db, story_id, account_id)
        illustration = get_story_illustration(db, story_id)
        if illustration is None or not illustration.image_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Illustration not found",
            )
        return {"image_url": self._image_storage.normalize_public_url(illustration.image_url) or illustration.image_url}

    def get_story_illustrations(self, db: Session, account_id: int, story_id: int) -> list[dict[str, Any]]:
        get_story_for_account(db, story_id, account_id)
        illustrations = list_story_illustrations(db, story_id)
        return [
            {
                "scene_id": item["scene_id"],
                "scene_order": item["scene_order"],
                "image_url": self._image_storage.normalize_public_url(item["image_url"]),
                "prompt_used": item["prompt_used"],
                "generation_model": item["generation_model"],
                "generated_at": item["generated_at"],
            }
            for item in illustrations
        ]
