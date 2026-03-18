from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException

from backend.character_canon.batch_service import (
    apply_reader_world_relationship_suggestions,
    build_batch_scope,
    enhance_reader_world_characters,
    suggest_reader_world_relationships,
)
from backend.db.database import SessionLocal
from backend.db.schema_migrations import ensure_character_canon_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enhance character canon and relationships across reader universes."
    )
    parser.add_argument("--apply", action="store_true", help="Write relationship and canon updates to the database")
    parser.add_argument("--reader-id", type=int, default=None, help="Limit the run to one reader")
    parser.add_argument("--world-id", type=int, default=None, help="Limit the run to one template world")
    parser.add_argument("--canon-only", action="store_true", help="Skip relationship suggestion/apply")
    parser.add_argument("--relationships-only", action="store_true", help="Skip character canon enhancement")
    parser.add_argument("--force", action="store_true", help="Re-enhance characters even if they already have canon")
    parser.add_argument(
        "--max-new-relationships",
        type=int,
        default=4,
        help="Maximum number of new relationships to suggest per reader world",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory where per-reader-world JSON packages and summary files are written",
    )
    return parser.parse_args()


def _default_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("character_canon_runs") / timestamp


def _sanitize_name(value: str | None) -> str:
    raw = (value or "reader_world").strip().lower()
    cleaned = "".join(character if character.isalnum() else "_" for character in raw)
    compact = "_".join(part for part in cleaned.split("_") if part)
    return compact or "reader_world"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    if args.canon_only and args.relationships_only:
        raise SystemExit("Choose either --canon-only or --relationships-only, not both.")

    ensure_character_canon_schema()

    run_relationships = not args.canon_only
    run_canon = not args.relationships_only

    db = SessionLocal()
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        scope = build_batch_scope(db, reader_id=args.reader_id, world_id=args.world_id)
        summary: dict[str, object] = {
            "applied": args.apply,
            "processed_reader_worlds": 0,
            "reader_worlds_with_errors": 0,
            "reader_worlds": [],
        }

        for item in scope:
            summary["processed_reader_worlds"] = int(summary["processed_reader_worlds"]) + 1
            logging.info(
                "processing reader %s / world %s (%s)",
                item["reader_id"],
                item["world_id"],
                item["world_name"] or "Unnamed World",
            )

            world_report = {
                "account_id": item["account_id"],
                "reader_id": item["reader_id"],
                "reader_name": item["reader_name"],
                "reader_world_id": item["reader_world_id"],
                "world_id": item["world_id"],
                "world_name": item["world_name"],
                "relationships": {
                    "status": "skipped",
                    "suggested": [],
                    "applied_count": 0,
                    "error": None,
                },
                "characters": [],
                "errors": [],
            }

            if run_relationships and item["world_id"] is not None:
                try:
                    suggestions = suggest_reader_world_relationships(
                        db,
                        account_id=int(item["account_id"]),
                        reader_id=int(item["reader_id"]),
                        world_id=int(item["world_id"]),
                        max_new_relationships=args.max_new_relationships,
                    )
                    world_report["relationships"]["suggested"] = suggestions
                    world_report["relationships"]["status"] = "suggested"
                    if args.apply and suggestions:
                        applied = apply_reader_world_relationship_suggestions(
                            db,
                            account_id=int(item["account_id"]),
                            reader_id=int(item["reader_id"]),
                            world_id=int(item["world_id"]),
                            suggestions=suggestions,
                        )
                        world_report["relationships"]["status"] = "applied"
                        world_report["relationships"]["applied_count"] = len(applied)
                except HTTPException as exc:
                    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                    world_report["relationships"]["status"] = "failed"
                    world_report["relationships"]["error"] = message
                    world_report["errors"].append(f"relationships: {message}")
                except Exception as exc:  # pragma: no cover - batch guard
                    world_report["relationships"]["status"] = "failed"
                    world_report["relationships"]["error"] = str(exc)
                    world_report["errors"].append(f"relationships: {exc}")

            if run_canon and item["world_id"] is not None:
                character_results = enhance_reader_world_characters(
                    db,
                    account_id=int(item["account_id"]),
                    reader_id=int(item["reader_id"]),
                    world_id=int(item["world_id"]),
                    apply_changes=args.apply,
                    force=args.force,
                )
                world_report["characters"] = [
                    {
                        "character_id": result.character_id,
                        "name": result.name,
                        "status": result.status,
                        "canon_version": result.canon_version,
                        "source_status": result.source_status,
                        "error": result.error,
                    }
                    for result in character_results
                ]
                failed_results = [result for result in character_results if result.error]
                world_report["errors"].extend(
                    [f"character {result.character_id}: {result.error}" for result in failed_results]
                )

            if world_report["errors"]:
                summary["reader_worlds_with_errors"] = int(summary["reader_worlds_with_errors"]) + 1

            filename = (
                f"reader_{int(item['reader_id']):03d}_world_{int(item['world_id'] or 0):03d}_"
                f"{_sanitize_name(str(item['world_name']))}.json"
            )
            output_path = output_dir / filename
            output_path.write_text(json.dumps(world_report, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.info("saved %s", output_path)
            summary["reader_worlds"].append(world_report)

        summary_path = output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info("processed reader worlds: %s", summary["processed_reader_worlds"])
        logging.info("reader worlds with errors: %s", summary["reader_worlds_with_errors"])
        logging.info("summary: %s", summary_path)
    finally:
        db.close()


if __name__ == "__main__":
    main()
