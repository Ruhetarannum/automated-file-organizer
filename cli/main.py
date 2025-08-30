from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from organizer.file_mover import FileMover
from organizer.logger import setup_logger


def load_config(config_path: str | Path) -> dict:
    if isinstance(config_path, Path):
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    else:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"{config_path} not found!")
        with open(config_path, "r") as f:
            return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="automated-file-organizer",
        description="Organize files from a source folder into categorized destinations.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.json (defaults to project_root/config/config.json)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Override source folder (otherwise taken from config).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print logs to console (in addition to file).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be moved without actually moving them.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files at destination (default: False).",
    )

    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    default_config = project_root / "config" / "config.json"
    config_path = Path(args.config) if args.config else default_config

    cfg = load_config(config_path)
    source = Path(args.source) if args.source else Path(cfg["source_folder"])
    dests = cfg["destination_folders"]  # dict[str, str]

    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(str(logs_dir / "organizer.log"), to_console=args.verbose)

    mover = FileMover(source_folder=str(source), dest_folders=dests, logger=logger)
    logger.info("Starting organization…")
    mover.organize(dry_run=args.dry_run, overwrite=args.overwrite)
    logger.info("Organization complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
