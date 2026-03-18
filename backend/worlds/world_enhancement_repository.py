from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table, TIMESTAMP, Text, delete, select, update
from sqlalchemy.orm import Session


metadata = MetaData()

worlds_table = Table(
    "worlds",
    metadata,
    Column("world_id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("description", Text),
    Column("default_world", Integer),
    Column("updated_at", TIMESTAMP),
)

world_rules_table = Table(
    "world_rules",
    metadata,
    Column("rule_id", Integer, primary_key=True),
    Column("world_id", Integer, nullable=False),
    Column("rule_type", String(100)),
    Column("rule_description", Text),
    Column("created_at", TIMESTAMP),
)

locations_table = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("description", Text),
)

characters_table = Table(
    "characters",
    metadata,
    Column("character_id", Integer, primary_key=True),
    Column("world_id", Integer),
    Column("name", String(255)),
    Column("species", String(100)),
    Column("personality_traits", Text),
    Column("home_location", Integer),
    Column("updated_at", TIMESTAMP),
)

character_relationships_table = Table(
    "character_relationships",
    metadata,
    Column("relationship_id", Integer, primary_key=True),
    Column("character_a", Integer),
    Column("character_b", Integer),
    Column("relationship_type", String(100)),
    Column("relationship_strength", Integer),
    Column("last_interaction", TIMESTAMP),
)


@dataclass
class WorldContextRecord:
    world_id: int
    name: str | None
    description: str | None
    default_world: bool | None
    updated_at: datetime | None
    locations: list[dict[str, Any]]
    characters: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    world_rules: list[dict[str, Any]]


def _decode_traits(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [part.strip() for part in stripped.split(",") if part.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return []


def load_world_context_for_enhancement(db: Session, world_id: int) -> WorldContextRecord | None:
    world_row = db.execute(
        select(worlds_table).where(worlds_table.c.world_id == world_id)
    ).mappings().first()
    if world_row is None:
        return None

    location_rows = db.execute(
        select(locations_table)
        .where(locations_table.c.world_id == world_id)
        .order_by(locations_table.c.location_id.asc())
    ).mappings().all()

    character_rows = db.execute(
        select(characters_table)
        .where(characters_table.c.world_id == world_id)
        .order_by(characters_table.c.character_id.asc())
    ).mappings().all()

    character_ids = [row.character_id for row in character_rows]
    relationship_rows: list[Any] = []
    if character_ids:
        relationship_rows = db.execute(
            select(character_relationships_table)
            .where(character_relationships_table.c.character_a.in_(character_ids))
            .where(character_relationships_table.c.character_b.in_(character_ids))
            .order_by(character_relationships_table.c.relationship_id.asc())
        ).mappings().all()

    rule_rows = db.execute(
        select(world_rules_table)
        .where(world_rules_table.c.world_id == world_id)
        .order_by(world_rules_table.c.rule_id.asc())
    ).mappings().all()

    character_name_lookup = {row.character_id: row.name for row in character_rows}

    return WorldContextRecord(
        world_id=world_row.world_id,
        name=world_row.name,
        description=world_row.description,
        default_world=world_row.default_world,
        updated_at=world_row.updated_at,
        locations=[
            {
                "location_id": row.location_id,
                "name": row.name,
                "description": row.description,
            }
            for row in location_rows
        ],
        characters=[
            {
                "character_id": row.character_id,
                "name": row.name,
                "species": row.species,
                "personality_traits": _decode_traits(row.personality_traits),
                "home_location": row.home_location,
            }
            for row in character_rows
        ],
        relationships=[
            {
                "relationship_id": row.relationship_id,
                "character_a": row.character_a,
                "character_a_name": character_name_lookup.get(row.character_a),
                "character_b": row.character_b,
                "character_b_name": character_name_lookup.get(row.character_b),
                "relationship_type": row.relationship_type,
                "relationship_strength": row.relationship_strength,
            }
            for row in relationship_rows
        ],
        world_rules=[
            {
                "rule_id": row.rule_id,
                "rule_type": row.rule_type,
                "rule_description": row.rule_description,
            }
            for row in rule_rows
        ],
    )


def replace_world_content(
    db: Session,
    world_id: int,
    package: dict[str, Any],
) -> dict[str, int]:
    world_payload = package["world"]
    location_payloads = package["locations"]
    character_payloads = package["characters"]
    relationship_payloads = package["relationships"]
    rule_payloads = package["world_rules"]

    existing_character_ids = db.execute(
        select(characters_table.c.character_id).where(characters_table.c.world_id == world_id)
    ).scalars().all()

    if existing_character_ids:
        db.execute(
            delete(character_relationships_table)
            .where(character_relationships_table.c.character_a.in_(existing_character_ids))
            .where(character_relationships_table.c.character_b.in_(existing_character_ids))
        )

    db.execute(delete(world_rules_table).where(world_rules_table.c.world_id == world_id))
    db.execute(delete(characters_table).where(characters_table.c.world_id == world_id))
    db.execute(delete(locations_table).where(locations_table.c.world_id == world_id))
    db.execute(
        update(worlds_table)
        .where(worlds_table.c.world_id == world_id)
        .values(
            name=world_payload["name"],
            description=world_payload["description"],
        )
    )

    location_id_by_name: dict[str, int] = {}
    for item in location_payloads:
        result = db.execute(
            locations_table.insert().values(
                world_id=world_id,
                name=item["name"],
                description=item["description"],
            )
        )
        location_id_by_name[item["name"]] = int(result.inserted_primary_key[0])

    character_id_by_name: dict[str, int] = {}
    for item in character_payloads:
        result = db.execute(
            characters_table.insert().values(
                world_id=world_id,
                name=item["name"],
                species=item["species"],
                personality_traits=json.dumps(item["personality_traits"], ensure_ascii=False),
                home_location=location_id_by_name[item["home_location_name"]],
            )
        )
        character_id_by_name[item["name"]] = int(result.inserted_primary_key[0])

    for item in relationship_payloads:
        db.execute(
            character_relationships_table.insert().values(
                character_a=character_id_by_name[item["character_a_name"]],
                character_b=character_id_by_name[item["character_b_name"]],
                relationship_type=item["relationship_type"],
                relationship_strength=item["relationship_strength"],
            )
        )

    for item in rule_payloads:
        db.execute(
            world_rules_table.insert().values(
                world_id=world_id,
                rule_type=item["rule_type"],
                rule_description=item["rule_description"],
            )
        )

    return {
        "locations_replaced": len(location_payloads),
        "characters_replaced": len(character_payloads),
        "relationships_replaced": len(relationship_payloads),
        "rules_replaced": len(rule_payloads),
    }
