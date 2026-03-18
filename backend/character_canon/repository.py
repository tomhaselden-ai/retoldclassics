from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, func, select
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Session


metadata = MetaData()

character_canon_profiles_table = Table(
    "character_canon_profiles",
    metadata,
    Column("canon_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("character_id", Integer, nullable=False),
    Column("world_id", Integer, nullable=False),
    Column("reader_world_id", Integer, nullable=False),
    Column("name", String(255)),
    Column("role_in_world", String(255)),
    Column("species_or_type", String(100)),
    Column("age_category", String(100)),
    Column("gender_presentation", String(100)),
    Column("archetype", String(255)),
    Column("one_sentence_essence", Text),
    Column("full_personality_summary", Text),
    Column("dominant_traits", JSON),
    Column("secondary_traits", JSON),
    Column("core_motivations", JSON),
    Column("fears_and_vulnerabilities", JSON),
    Column("moral_tendencies", JSON),
    Column("behavioral_rules_usually", JSON),
    Column("behavioral_rules_never", JSON),
    Column("behavioral_rules_requires_justification", JSON),
    Column("speech_style", Text),
    Column("signature_expressions", JSON),
    Column("relationship_tendencies", Text),
    Column("growth_arc_pattern", Text),
    Column("continuity_anchors", JSON),
    Column("visual_summary", Text),
    Column("form_type", String(100)),
    Column("anthropomorphic_level", String(100)),
    Column("size_and_proportions", Text),
    Column("silhouette_description", Text),
    Column("facial_features", Text),
    Column("eye_description", Text),
    Column("fur_skin_surface_description", Text),
    Column("hair_feather_tail_details", Text),
    Column("clothing_and_accessories", Text),
    Column("signature_physical_features", JSON),
    Column("expression_range", Text),
    Column("movement_pose_tendencies", Text),
    Column("color_palette", JSON),
    Column("art_style_constraints", Text),
    Column("visual_must_never_change", JSON),
    Column("visual_may_change", JSON),
    Column("narrative_prompt_pack_short", Text),
    Column("visual_prompt_pack_short", Text),
    Column("continuity_lock_pack", Text),
    Column("source_status", String(20)),
    Column("canon_version", Integer),
    Column("enhanced_at", TIMESTAMP),
    Column("enhanced_by", Integer),
    Column("last_reviewed_at", TIMESTAMP),
    Column("is_major_character", Integer),
    Column("is_locked", Integer),
    Column("notes", Text),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

character_canon_versions_table = Table(
    "character_canon_versions",
    metadata,
    Column("version_id", Integer, primary_key=True),
    Column("canon_id", Integer, nullable=False),
    Column("account_id", Integer, nullable=False),
    Column("character_id", Integer, nullable=False),
    Column("reader_world_id", Integer, nullable=False),
    Column("canon_version", Integer, nullable=False),
    Column("source_status", String(20)),
    Column("snapshot_json", JSON),
    Column("created_by", Integer),
    Column("created_at", TIMESTAMP),
)

character_canon_enhancement_runs_table = Table(
    "character_canon_enhancement_runs",
    metadata,
    Column("enhancement_run_id", Integer, primary_key=True),
    Column("account_id", Integer, nullable=False),
    Column("character_id", Integer, nullable=False),
    Column("world_id", Integer, nullable=False),
    Column("reader_world_id", Integer, nullable=False),
    Column("section_mode", String(20)),
    Column("status", String(20)),
    Column("prompt_context_json", JSON),
    Column("generated_profile_json", JSON),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
    Column("applied_at", TIMESTAMP),
)


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def get_character_canon_profile(
    db: Session,
    *,
    account_id: int,
    reader_world_id: int,
    character_id: int,
) -> dict[str, Any] | None:
    row = db.execute(
        select(character_canon_profiles_table)
        .where(character_canon_profiles_table.c.account_id == account_id)
        .where(character_canon_profiles_table.c.reader_world_id == reader_world_id)
        .where(character_canon_profiles_table.c.character_id == character_id)
    ).mappings().first()
    return _row_to_dict(row)


def list_character_canon_profiles(
    db: Session,
    *,
    account_id: int,
    reader_world_id: int,
    character_ids: list[int],
) -> dict[int, dict[str, Any]]:
    if not character_ids:
        return {}
    rows = db.execute(
        select(character_canon_profiles_table)
        .where(character_canon_profiles_table.c.account_id == account_id)
        .where(character_canon_profiles_table.c.reader_world_id == reader_world_id)
        .where(character_canon_profiles_table.c.character_id.in_(character_ids))
    ).mappings().all()
    payload: dict[int, dict[str, Any]] = {}
    for row in rows:
        record = _row_to_dict(row)
        if record is None:
            continue
        payload[int(record["character_id"])] = record
    return payload


def upsert_character_canon_profile(
    db: Session,
    *,
    account_id: int,
    reader_world_id: int,
    character_id: int,
    profile: dict[str, Any],
) -> dict[str, Any]:
    existing = get_character_canon_profile(
        db,
        account_id=account_id,
        reader_world_id=reader_world_id,
        character_id=character_id,
    )

    values = {
        key: value
        for key, value in profile.items()
        if key in character_canon_profiles_table.c
    }
    values["account_id"] = account_id
    values["reader_world_id"] = reader_world_id
    values["character_id"] = character_id

    if existing is None:
        result = db.execute(character_canon_profiles_table.insert().values(**values))
        canon_id = int(result.inserted_primary_key[0])
    else:
        canon_id = int(existing["canon_id"])
        db.execute(
            character_canon_profiles_table.update()
            .where(character_canon_profiles_table.c.canon_id == canon_id)
            .values(**values)
        )

    row = db.execute(
        select(character_canon_profiles_table)
        .where(character_canon_profiles_table.c.canon_id == canon_id)
    ).mappings().first()
    record = _row_to_dict(row)
    if record is None:
        raise RuntimeError("Character canon profile could not be stored")
    return record


def insert_character_canon_version(
    db: Session,
    *,
    canon_id: int,
    account_id: int,
    character_id: int,
    reader_world_id: int,
    canon_version: int,
    source_status: str | None,
    snapshot_json: dict[str, Any],
    created_by: int | None,
) -> dict[str, Any]:
    result = db.execute(
        character_canon_versions_table.insert().values(
            canon_id=canon_id,
            account_id=account_id,
            character_id=character_id,
            reader_world_id=reader_world_id,
            canon_version=canon_version,
            source_status=source_status,
            snapshot_json=snapshot_json,
            created_by=created_by,
        )
    )
    version_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(character_canon_versions_table)
        .where(character_canon_versions_table.c.version_id == version_id)
    ).mappings().first()
    record = _row_to_dict(row)
    if record is None:
        raise RuntimeError("Character canon version could not be stored")
    return record


def list_character_canon_versions(
    db: Session,
    *,
    account_id: int,
    reader_world_id: int,
    character_id: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(character_canon_versions_table)
        .where(character_canon_versions_table.c.account_id == account_id)
        .where(character_canon_versions_table.c.reader_world_id == reader_world_id)
        .where(character_canon_versions_table.c.character_id == character_id)
        .order_by(character_canon_versions_table.c.canon_version.desc())
        .limit(limit)
    ).mappings().all()
    return [dict(row) for row in rows]


def insert_character_canon_enhancement_run(
    db: Session,
    *,
    account_id: int,
    character_id: int,
    world_id: int,
    reader_world_id: int,
    section_mode: str,
    status: str,
    prompt_context_json: dict[str, Any],
    generated_profile_json: dict[str, Any],
) -> dict[str, Any]:
    result = db.execute(
        character_canon_enhancement_runs_table.insert().values(
            account_id=account_id,
            character_id=character_id,
            world_id=world_id,
            reader_world_id=reader_world_id,
            section_mode=section_mode,
            status=status,
            prompt_context_json=prompt_context_json,
            generated_profile_json=generated_profile_json,
        )
    )
    enhancement_run_id = int(result.inserted_primary_key[0])
    row = db.execute(
        select(character_canon_enhancement_runs_table)
        .where(character_canon_enhancement_runs_table.c.enhancement_run_id == enhancement_run_id)
    ).mappings().first()
    record = _row_to_dict(row)
    if record is None:
        raise RuntimeError("Character enhancement run could not be stored")
    return record


def update_character_canon_enhancement_run_status(
    db: Session,
    *,
    enhancement_run_id: int,
    status: str,
    applied: bool = False,
) -> dict[str, Any] | None:
    values: dict[str, Any] = {"status": status}
    if applied:
        values["applied_at"] = func.now()

    db.execute(
        character_canon_enhancement_runs_table.update()
        .where(character_canon_enhancement_runs_table.c.enhancement_run_id == enhancement_run_id)
        .values(**values)
    )

    row = db.execute(
        select(character_canon_enhancement_runs_table)
        .where(character_canon_enhancement_runs_table.c.enhancement_run_id == enhancement_run_id)
    ).mappings().first()
    return _row_to_dict(row)


def mark_character_canon_enhancement_run_applied(
    db: Session,
    *,
    enhancement_run_id: int,
) -> dict[str, Any] | None:
    db.execute(
        character_canon_enhancement_runs_table.update()
        .where(character_canon_enhancement_runs_table.c.enhancement_run_id == enhancement_run_id)
        .values(status="applied", applied_at=func.now())
    )
    row = db.execute(
        select(character_canon_enhancement_runs_table)
        .where(character_canon_enhancement_runs_table.c.enhancement_run_id == enhancement_run_id)
    ).mappings().first()
    return _row_to_dict(row)


def list_character_canon_enhancement_runs(
    db: Session,
    *,
    account_id: int,
    reader_world_id: int,
    character_id: int,
    limit: int = 10,
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(character_canon_enhancement_runs_table)
        .where(character_canon_enhancement_runs_table.c.account_id == account_id)
        .where(character_canon_enhancement_runs_table.c.reader_world_id == reader_world_id)
        .where(character_canon_enhancement_runs_table.c.character_id == character_id)
        .order_by(character_canon_enhancement_runs_table.c.enhancement_run_id.desc())
        .limit(limit)
    ).mappings().all()
    return [dict(row) for row in rows]
