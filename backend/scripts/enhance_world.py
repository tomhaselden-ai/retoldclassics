import argparse
import json
import logging
from pathlib import Path

from backend.db.database import SessionLocal
from backend.worlds.world_enhancement_service import enhance_world


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft or apply a world enhancement package.")
    parser.add_argument("--world-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", type=str, default=None, help="Optional path to save the generated package JSON")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    db = SessionLocal()

    try:
        result = enhance_world(
            db=db,
            world_id=args.world_id,
            apply_changes=args.apply,
        )
        logging.info("world_id: %s", result.world_id)
        logging.info("world_name: %s", result.world_name)
        logging.info("applied: %s", "yes" if result.applied else "no")
        for key, value in result.summary.items():
            logging.info("%s: %s", key, value)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result.package, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.info("saved_package: %s", output_path)
        else:
            logging.info(json.dumps(result.package, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
