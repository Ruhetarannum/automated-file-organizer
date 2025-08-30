"""Main entry point for the automated file organizer CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from .file_mover import FileMover, load_config
from .logger import setup_logger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="organizer",
        description="Organize files from a source folder into categorized destinations",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.json (optional, overrides auto-detection)",
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

    project_root = Path.cwd()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(str(logs_dir / "organizer.log"), to_console=args.verbose)

    try:
        # If source passed → ignore config and use built-in categories
        if args.source:
            source = Path(args.source)
            mover = FileMover(source_folder=str(source), dest_folders={}, logger=logger)
            logger.info("Starting organization using built-in categories…")
            mover.organize(dry_run=args.dry_run, overwrite=args.overwrite)
            logger.info("Organization complete.")
            return 0

        # Otherwise → load config (auto-generates if missing)
        cfg = load_config() if args.config is None else load_config(Path(args.config))
        if cfg is None:
            print("Error: Failed to load or generate configuration.")
            return 1

        source = Path(cfg["source_folder"])
        dests = cfg["destination_folders"]

        mover = FileMover(source_folder=str(source), dest_folders=dests, logger=logger)
        logger.info("Starting organization using config file…")
        mover.organize(dry_run=args.dry_run, overwrite=args.overwrite)
        logger.info("Organization complete.")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


__all__ = ["main"]
