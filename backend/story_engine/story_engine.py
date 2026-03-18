import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.character_canon.repository import list_character_canon_profiles
from backend.story_engine.prompt_builder import build_story_prompt
from backend.story_engine.requested_character_service import resolve_required_story_character
from backend.story_engine.retrieval_service import retrieve_classical_guidance
from backend.story_engine.story_events import capture_generated_story_events
from backend.story_engine.story_generator import generate_story
from backend.story_engine.story_repository import (
    create_generated_story,
    create_story_scene,
    load_reader,
)
from backend.worlds.reader_world_context import get_reader_world_assignment, load_reader_world_context
from backend.vocabulary.vocabulary_service import extract_story_vocabulary


def _ensure_reader_belongs_to_account(reader: Any, account_id: int) -> None:
    if reader.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reader does not belong to this account",
        )


def generate_story_for_reader(
    db: Session,
    account_id: int,
    reader_id: int,
    world_id: int,
    theme: str,
    target_length: str,
) -> dict[str, Any]:
    logging.info("Starting story generation for reader %s", reader_id)

    reader = load_reader(db, reader_id)
    _ensure_reader_belongs_to_account(reader, account_id)

    reader_world, _ = get_reader_world_assignment(db, reader_id, world_id)
    world_context = load_reader_world_context(db, reader_world.reader_world_id)

    required_story_character = resolve_required_story_character(
        db=db,
        reader_world_id=reader_world.reader_world_id,
        theme=theme,
        world_context=world_context,
    )
    if required_story_character and required_story_character.get("created"):
        world_context = load_reader_world_context(db, reader_world.reader_world_id)

    classical_chunks = retrieve_classical_guidance(
        theme=theme,
        reader_profile=reader,
        world_context=world_context,
    )
    canon_lookup = list_character_canon_profiles(
        db,
        account_id=account_id,
        reader_world_id=reader_world.reader_world_id,
        character_ids=[
            character.character_id
            for character in world_context["characters"]
            if isinstance(getattr(character, "character_id", None), int)
        ],
    )

    try:
        prompt_messages = build_story_prompt(
            reader_profile=reader,
            reader_world=reader_world,
            world_context=world_context,
            classical_chunks=classical_chunks,
            theme=theme,
            target_length=target_length,
            required_story_character=required_story_character,
            character_canon_lookup=canon_lookup,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    story_payload = generate_story(prompt_messages)

    try:
        story_id = create_generated_story(
            db=db,
            reader_id=reader.reader_id,
            reader_world_id=reader_world.reader_world_id,
            title=story_payload["title"],
            trait_focus=theme,
        )

        scenes = story_payload.get("scenes", [])
        for index, scene in enumerate(scenes, start=1):
            create_story_scene(
                db=db,
                story_id=story_id,
                scene_order=index,
                scene_payload=scene,
            )

        capture_generated_story_events(
            db=db,
            story_id=story_id,
            scenes=[scene for scene in scenes if isinstance(scene, dict)],
            world_context=world_context,
        )

        extract_story_vocabulary(
            db=db,
            reader_id=reader.reader_id,
            story_id=story_id,
            reading_level=reader.reading_level,
        )

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save generated story",
        ) from exc

    return {
        "story_id": story_id,
        "title": story_payload["title"],
        "summary": story_payload.get("summary", ""),
    }
