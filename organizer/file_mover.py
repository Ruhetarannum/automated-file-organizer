"""File organization module for automated file categorization and movement.

This module provides functionality to automatically organize files based on their
extensions into predefined categories. It supports both built-in categorization
rules and user-defined configuration files.

Main components:
    - FileMover class: Core file organization functionality
    - Configuration system: User-customizable file categorization rules
    - Built-in categories: Default categorization for common file types
    - Utility functions: Config loading, caching, and file operations

Example:
    Basic usage:
    >>> mover = FileMover('/path/to/source', {}, logger=my_logger)
    >>> mover.organize(dry_run=True)  # Preview what would happen
    >>> mover.organize()  # Actually organize files

Author: Automated File Organizer Project
Version: 1.0.0
"""

import json
import logging
import shutil
import time
from pathlib import Path

# Module-level logger for all file operations
logger = logging.getLogger(__name__)

# Global cache for storing loaded configuration data to avoid repeated file I/O
# This cache is cleared when config needs to be reloaded

logger = logging.getLogger(__name__)


def load_config() -> dict | None:
    """
    Load user configuration from `.fileorganizer.json`.

    - Searches upward from the current working directory.
    - If not found, auto-generates a default `.fileorganizer.json`.
    - Returns a dict with "source_folder" and "destination_folders".
    """
    try:
        current_dir = Path.cwd()
        config_path = None

        # Search for existing config
        for parent in [current_dir] + list(current_dir.parents):
            potential = parent / ".fileorganizer.json"
            if potential.exists():
                config_path = potential
                break

        # If not found → auto-generate
        if config_path is None:
            config_path = current_dir / ".fileorganizer.json"
            default_config = {
                "source_folder": str(current_dir),
                "destination_folders": {
                    "Documents": str(current_dir / "Documents"),
                    "Images": str(current_dir / "Images"),
                    "Videos": str(current_dir / "Videos"),
                    "Music": str(current_dir / "Music"),
                    "Archives": str(current_dir / "Archives"),
                    "Code": str(current_dir / "Code"),
                    "Others": str(current_dir / "Others"),
                },
            }
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"No config found. Default config generated at {config_path}")
            return default_config

        # Load and validate existing config
        with config_path.open("r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Validate config structure
        if not isinstance(config_data, dict):
            logger.warning("Invalid config: root must be a JSON object")
            return None

        if "source_folder" not in config_data or "destination_folders" not in config_data:
            logger.warning("Invalid config: must contain 'source_folder' and 'destination_folders'")
            return None

        logger.info(f"Loaded config from {config_path}")
        return config_data

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to parse config file: {e}")

        return None

    except Exception as e:
        logger.warning(f"Unexpected error loading config: {e}")
        return None


class FileMover:
    """
    Main class for file organization.

    Attributes:
        source_folder (str): Path to the source directory to organize.
        dest_folders (dict[str, str]): Mapping of categories to destination paths.
        logger (logging.Logger): Logger instance for operation tracking.
    """

    def __init__(self, source_folder, dest_folders: dict[str, str], logger=None):
        """
        Initialize the FileMover instance.

        Args:
            source_folder (str): Path to the source directory to organize.
            dest_folders (dict[str, str]): Mapping of categories to destination paths.
            logger (logging.Logger, optional): Logger instance for operation tracking.
        """
        # Store source folder path - kept as raw value for compatibility with existing tests
        # that expect string type rather than Path object
        self.source_folder = source_folder

        # Legacy destination folders mapping - kept for backward compatibility
        # but not actively used in current categorization logic
        self.dest_folders = dest_folders

        # Initialize logger - use provided logger or fall back to module default
        self.logger = logger or logging.getLogger(__name__)

    def scan_directory(self, directory_path=None):
        """
        Scan a directory and collect all files recursively.

        Args:
            directory_path (str, optional): Path to the directory to scan.

        Returns:
            list[str]: List of absolute file paths in the directory.
        """
        # Use provided path or fall back to instance's source folder
        base_path = Path(directory_path or self.source_folder)

        # Attempt to resolve the path to an absolute path
        # This handles symbolic links and relative paths
        try:
            base_path = base_path.resolve()
        except Exception:
            # If resolution fails (e.g., broken symlinks), proceed with the given path
            # This allows the function to continue rather than failing completely
            pass

        # Validate that the path exists and is actually a directory
        if not base_path.exists() or not base_path.is_dir():
            if self.logger:
                self.logger.warning(f"Directory does not exist or is not a directory: {base_path}")
            return []  # Return empty list for invalid directories

        # Collect all files recursively
        files = []
        for path in base_path.rglob("*"):  # rglob("*") finds all items recursively
            if path.is_file():  # Only include files, not directories
                try:
                    # Try to get absolute path for consistency
                    files.append(str(path.resolve()))
                except Exception:
                    # Fallback to string representation if resolve fails
                    # This handles edge cases like broken symlinks or permission issues
                    files.append(str(path))

        # Log the results for tracking and debugging
        if self.logger:
            self.logger.info(f"Scanned {base_path}: found {len(files)} files")

        return files

    def categorize_file(self, file_path):
        """Categorize a file based on its extension."""
        # Extract file extension and normalize to lowercase for consistent matching
        suffix = Path(file_path).suffix.lower()

        # Try to load config file first
        config = load_config()
        if config:
            # Use config file categories
            for category, extensions in config.items():
                if suffix in extensions:
                    return category.lower()

        # Fall back to built-in categories if no config or no match found
        extension_to_category = {
            # Images
            ".jpg": "images",
            ".jpeg": "images",
            ".png": "images",
            ".gif": "images",
            ".bmp": "images",
            ".tiff": "images",
            ".webp": "images",
            # Documents
            ".pdf": "documents",
            ".doc": "documents",
            ".docx": "documents",
            ".txt": "documents",
            ".rtf": "documents",
            ".odt": "documents",
            ".xls": "documents",
            ".xlsx": "documents",
            ".ppt": "documents",
            ".pptx": "documents",
            # Videos
            ".mp4": "videos",
            ".mov": "videos",
            ".avi": "videos",
            ".mkv": "videos",
            ".wmv": "videos",
            ".flv": "videos",
            ".webm": "videos",
            # Music
            ".mp3": "music",
            ".wav": "music",
            ".flac": "music",
            ".aac": "music",
            # Archives
            ".zip": "archives",
            ".rar": "archives",
            ".tar": "archives",
            ".gz": "archives",
            ".7z": "archives",
            # Code
            ".py": "code",
            ".java": "code",
            ".cpp": "code",
            ".js": "code",
            ".ts": "code",
            ".html": "code",
            ".css": "code",
        }

        return extension_to_category.get(suffix, "others")

    def move_file(self, file_path, category=None, overwrite: bool = False):
        """
        Move a file to the appropriate category within the source folder.

        Args:
            file_path (str): The path to the file to be moved.
            category (str, optional): The category to which the file should be moved.
            overwrite (bool, optional):If True, overwrite existing files in destination folder.
        """
        # Convert file_path to Path object for consistent handling
        source_path = Path(file_path)
        # If a bare filename is provided, resolve it under the configured source folder
        if not source_path.is_absolute():
            source_path = Path(self.source_folder) / source_path

        if not source_path.exists() or not source_path.is_file():
            if self.logger:
                self.logger.warning(f"File does not exist or is not a file: {source_path}")
            return

        destination_category = category or self.categorize_file(source_path)
        destination_root = Path(self.source_folder)
        destination_dir = destination_root / destination_category
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination_path = destination_dir / source_path.name

        try:
            # Handle overwrite logic directly
            if destination_path.exists() and not overwrite:
                if self.logger:
                    self.logger.error(f"Destination already exists and overwrite is False: {destination_path}")
                raise FileExistsError(f"Destination already exists: {destination_path}")

            # If overwrite is True, remove the existing destination
            if destination_path.exists() and overwrite:
                try:
                    if destination_path.is_dir():
                        shutil.rmtree(destination_path)
                    else:
                        destination_path.unlink()
                except Exception as exc:
                    if self.logger:
                        self.logger.error(
                            f"Failed to remove existing destination before overwrite: {destination_path}: {exc}",
                            exc_info=True,
                        )
                    raise

            # Move the file
            shutil.move(str(source_path), str(destination_path))
            if self.logger:
                self.logger.info(f"Moved '{source_path}' to '{destination_path}'")
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    f"Failed to move '{source_path}' to '{destination_path}': {exc}",
                    exc_info=True,
                )
            raise

    def organize(self, dry_run: bool = False, overwrite: bool = False):
        """
        Organize files in the source folder into their appropriate categories.

        Args:
            dry_run (bool, optional): If True, show what files would be moved without actually moving them.
            overwrite (bool, optional): If True,overwrite existing files in destination folders.
        """
        # Log the beginning of the organization operation
        if self.logger:
            self.logger.info(f"Organizing folder: {self.source_folder}")
            if dry_run:
                self.logger.info("DRY RUN MODE: No files will be moved")

        files = self.scan_directory(self.source_folder)

        for file_path in files:
            try:
                category = self.categorize_file(file_path)
                if self.logger:
                    self.logger.info(f"Categorized '{file_path}' as '{category}'")

                if dry_run:
                    # In dry-run mode, just show what would happen
                    destination_root = Path(self.source_folder)
                    destination_dir = destination_root / category
                    destination_path = destination_dir / Path(file_path).name

                    if destination_path.exists() and not overwrite:
                        self.logger.info(
                            f"[DRY RUN] Would skip '{file_path}' -> '{destination_path}' (destination exists)"
                        )
                    else:
                        self.logger.info(f"[DRY RUN] Would move '{file_path}' -> '{destination_path}'")
                else:
                    # Actually move the file
                    self.move_file(file_path, category, overwrite=overwrite)
            except Exception as exc:
                if self.logger:
                    self.logger.error(f"Failed to organize '{file_path}': {exc}", exc_info=True)

        if self.logger:
            if dry_run:
                self.logger.info("Dry run complete-no files were moved")
            else:
                self.logger.info("Organization complete")


def move_file(source: str, destination: str, overwrite: bool = False, max_retries: int = 3) -> None:
    """
    Move a file from one location to another.

    Args:
        source (str): The path to the source file.
        destination (str): The path to the destination folder.
        overwrite (bool, optional): If True,overwrite existing files in destination folder.
        max_retries (int, optional): The maximum number of retries for file lock errors.
    """
    src_path = Path(source)
    dest_path = Path(destination)

    if not src_path.exists() or not src_path.is_file():
        logger.error(f"Source file not found: {src_path}")
        raise FileNotFoundError(f"Source file not found: {src_path}")

    # Ensure parent directories exist
    dest_parent = dest_path.parent
    dest_parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        if not overwrite:
            logger.error(f"Destination already exists and overwrite is False: {dest_path}")
            raise FileExistsError(f"Destination already exists: {dest_path}")
        # If overwrite is True, remove the existing destination
        try:
            if dest_path.is_dir():
                shutil.rmtree(dest_path)
            else:
                dest_path.unlink()
        except Exception as exc:
            logger.error(
                f"Failed to remove existing destination before overwrite: {dest_path}: {exc}",
                exc_info=True,
            )
            raise

    # Retry mechanism for file lock errors
    for attempt in range(max_retries + 1):
        try:
            shutil.move(str(src_path), str(dest_path))
            logger.info(f"moved {src_path} -> {dest_path}")
            return  # Success, exit the function
        except PermissionError:
            if attempt < max_retries:
                # Wait before retrying (file might be temporarily locked)
                time.sleep(0.5)
                continue
            else:
                # Max retries reached, log and re-raise
                logger.error(f"File locked: {src_path}")
                raise
        except Exception as exc:
            logger.error(f"Failed to move {src_path} -> {dest_path}: {exc}", exc_info=True)
            raise
