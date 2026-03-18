import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException

from backend.db.database import SessionLocal
from backend.worlds.world_enhancement_service import enhance_world
from backend.worlds.world_service import list_worlds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft or apply world enhancements in batch.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--start-world-id", type=int, default=None)
    parser.add_argument("--end-world-id", type=int, default=None)
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory where per-world JSON packages and summary files are written",
    )
    return parser.parse_args()


def _default_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("world_enhancement_runs") / timestamp


def _sanitize_name(value: str | None) -> str:
    raw = (value or "world").strip().lower()
    cleaned = "".join(character if character.isalnum() else "_" for character in raw)
    compact = "_".join(part for part in cleaned.split("_") if part)
    return compact or "world"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    db = SessionLocal()

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        worlds = list_worlds(db)
        if args.start_world_id is not None:
            worlds = [world for world in worlds if world.world_id >= args.start_world_id]
        if args.end_world_id is not None:
            worlds = [world for world in worlds if world.world_id <= args.end_world_id]

        processed = 0
        succeeded = 0
        failed = 0
        error_records: list[dict[str, str | int]] = []

        for world in worlds:
            processed += 1
            logging.info("processing world %s - %s", world.world_id, world.name or "Unnamed World")
            try:
                result = enhance_world(
                    db=db,
                    world_id=world.world_id,
                    apply_changes=args.apply,
                )
                filename = f"{world.world_id:03d}_{_sanitize_name(result.world_name)}.json"
                output_path = output_dir / filename
                output_path.write_text(
                    json.dumps(result.package, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logging.info(
                    "saved world %s package to %s",
                    world.world_id,
                    output_path,
                )
                succeeded += 1
            except HTTPException as exc:
                failed += 1
                message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                logging.info("failed world %s - %s", world.world_id, message)
                error_records.append(
                    {
                        "world_id": world.world_id,
                        "world_name": world.name or "Unnamed World",
                        "error": message,
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive batch guard
                failed += 1
                logging.info("failed world %s - %s", world.world_id, str(exc))
                error_records.append(
                    {
                        "world_id": world.world_id,
                        "world_name": world.name or "Unnamed World",
                        "error": str(exc),
                    }
                )

        summary_payload = {
            "applied": args.apply,
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "errors": error_records,
        }
        summary_path = output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        logging.info("processed: %s", processed)
        logging.info("succeeded: %s", succeeded)
        logging.info("failed: %s", failed)
        logging.info("summary: %s", summary_path)
    finally:
        db.close()


if __name__ == "__main__":
    main()
