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

from pathlib import Path
import logging
import shutil
import time
import json

# Module-level logger for all file operations
logger = logging.getLogger(__name__)

# Global cache for storing loaded configuration data to avoid repeated file I/O
# This cache is cleared when config needs to be reloaded
_config_cache = None


def load_config():
    """
    Load and validate user configuration from .fileorganizer.json file.

    Searches for the configuration file starting from the current working directory
    and traversing up the directory tree until found. The config file should contain
    a JSON object mapping category names to lists of file extensions.

    Example config file format:
        {
            "Images": [".jpg", ".png", ".gif"],
            "Documents": [".pdf", ".docx", ".txt"],
            "CustomCategory": [".xyz", ".custom"]
        }

    The function performs extensive validation:
    - Ensures the file contains valid JSON
    - Verifies the root is a JSON object (not array or primitive)
    - Validates that each category maps to a list of extensions
    - Filters out invalid extensions (non-strings)
    - Caches the result to avoid repeated file I/O operations

    Returns:
        dict or None: Configuration mapping category names (strings) to lists
                     of file extensions (strings). Category names are used as-is
                     from the config file. Returns None if no config file is found,
                     the file is invalid, or no valid categories are defined.

    Note:
        The returned configuration is cached globally. Use clear_config_cache()
        to force reloading if the config file has been modified.
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None:
        return _config_cache

    try:
        # Look for .fileorganizer.json in current working directory and parent directories
        current_dir = Path.cwd()
        config_path = None

        # Search up the directory tree for the config file
        for parent in [current_dir] + list(current_dir.parents):
            potential_config = parent / ".fileorganizer.json"
            if potential_config.exists():
                config_path = potential_config
                break

        if config_path is None:
            logger.debug(
                "No .fileorganizer.json config file found, using built-in categories"
            )
            _config_cache = None
            return None

        # Load and parse the config file
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Validate config structure
        if not isinstance(config_data, dict):
            logger.warning("Invalid config file: root must be a JSON object")
            _config_cache = None
            return None

        # Validate each category has a list of extensions
        validated_config = {}
        for category, extensions in config_data.items():
            if not isinstance(extensions, list):
                logger.warning(
                    f"Invalid config for category '{category}': extensions must be a list"
                )
                continue

            # Filter out non-string extensions
            valid_extensions = [ext for ext in extensions if isinstance(ext, str)]
            if valid_extensions:
                validated_config[category] = valid_extensions
            else:
                logger.warning(f"Category '{category}' has no valid extensions")

        if not validated_config:
            logger.warning(
                "No valid categories found in config file, using built-in categories"
            )
            _config_cache = None
            return None

        logger.info(f"Loaded {len(validated_config)} categories from {config_path}")
        _config_cache = validated_config
        return validated_config

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to parse config file: {e}")
        _config_cache = None
        return None
    except Exception as e:
        logger.warning(f"Failed to load config file: {e}")
        _config_cache = None
        return None


def clear_config_cache():
    """
    Clear the cached configuration to force reloading from file.
    Useful when the config file has been modified.
    """
    global _config_cache
    _config_cache = None
    logger.debug("Configuration cache cleared")


class FileMover:
    """
    Core file organization class for automated file categorization and movement.

    FileMover provides functionality to scan directories, categorize files by extension,
    and move them into organized folder structures. It supports both user-defined
    configuration files and built-in categorization rules.

    Key Features:
    - Recursive directory scanning
    - File categorization based on extensions
    - Support for custom configuration files (.fileorganizer.json)
    - Built-in categorization for common file types
    - Dry-run mode for preview operations
    - Overwrite protection and conflict resolution
    - Comprehensive logging and error handling

    Attributes:
        source_folder (str): Path to the source directory to organize
        dest_folders (dict): Mapping of categories to destination paths (legacy)
        logger (logging.Logger): Logger instance for operation tracking

    Example:
        Basic usage:
        >>> mover = FileMover('/path/to/downloads', {})
        >>> mover.organize(dry_run=True)  # Preview mode
        >>> mover.organize()  # Actually organize files

        With custom logger:
        >>> import logging
        >>> logger = logging.getLogger('file_organizer')
        >>> mover = FileMover('/path/to/source', {}, logger=logger)
    """

    def __init__(self, source_folder, dest_folders: dict[str, str], logger=None):
        """
        Initialize the FileMover with source directory and configuration.

        Args:
            source_folder (str or Path): Path to the folder containing files to organize.
                                       This will be the root directory for scanning and
                                       the base directory for creating category subdirectories.
            dest_folders (dict[str, str]): Legacy parameter for destination folder mapping.
                                          Currently not used in the main categorization logic,
                                          but kept for backward compatibility with existing code.
                                          Example: {".txt": "Documents", ".jpg": "Images"}
            logger (logging.Logger, optional): Custom logger instance for tracking operations.
                                              If None, uses the module's default logger.
                                              Defaults to None.

        Note:
            The dest_folders parameter is maintained for compatibility but the actual
            categorization is handled by the categorize_file() method using either
            user config files or built-in rules.
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
        Recursively scan a directory and return all file paths without modifying them.

        This method performs a comprehensive scan of the specified directory (or the
        instance's source folder if none specified) and returns absolute paths to
        all files found. The scan is recursive, meaning it will find files in
        subdirectories as well.

        Args:
            directory_path (str or Path, optional): Path to the directory to scan.
                                                   If None, uses self.source_folder.
                                                   Can be either a string path or Path object.

        Returns:
            list[str]: List of absolute file paths (as strings) for all files found
                      in the directory tree. Returns empty list if directory doesn't
                      exist, is not a directory, or contains no files.

        Note:
            - Only files are returned, not directories
            - Paths are resolved to absolute paths when possible
            - If path resolution fails, falls back to string representation
            - The scan is logged for tracking purposes

        Example:
            >>> mover = FileMover('/path/to/source', {})
            >>> files = mover.scan_directory()
            >>> print(f"Found {len(files)} files to organize")
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
                self.logger.warning(
                    f"Directory does not exist or is not a directory: {base_path}"
                )
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
        """
        Determine the appropriate category for a file based on its extension.

        This method implements a two-tier categorization system:
        1. First, attempts to load and use user-defined categories from .fileorganizer.json
        2. If no config file exists or no match is found, falls back to built-in categories

        The categorization process:
        - Extracts the file extension (e.g., '.txt', '.jpg') and converts to lowercase
        - Searches user config file for matching extensions (case-insensitive)
        - If found in config, returns the corresponding category name (lowercased)
        - If not found in config, searches built-in category mappings
        - If no match in either system, returns "others" as default category

        Built-in Categories:
        - images: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp
        - documents: .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx
        - videos: .mp4, .mov, .avi, .mkv, .wmv, .flv, .webm
        - music: .mp3, .wav, .flac, .aac
        - archives: .zip, .rar, .tar, .gz, .7z
        - code: .py, .java, .cpp, .js, .ts, .html, .css
        - others: any extension not matching the above categories

        Args:
            file_path (str or Path): Path to the file to categorize. Only the extension
                                   is used for categorization; the file doesn't need to exist.
                                   Can be a full path, relative path, or just a filename.

        Returns:
            str: The category name (always lowercase) that the file should be placed in.
                Returns "others" if no specific category matches the file extension.

        Example:
            >>> mover = FileMover('/path/to/source', {})
            >>> mover.categorize_file('/path/to/document.pdf')
            'documents'
            >>> mover.categorize_file('image.JPG')  # case-insensitive
            'images'
            >>> mover.categorize_file('unknown.xyz')
            'others'

        Note:
            - Extension matching is case-insensitive
            - User config categories take priority over built-in categories
            - Category names from config are normalized to lowercase
            - The file doesn't need to exist; only the extension is analyzed
        """
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
        Move a single file to its appropriate category folder within the source directory.

        This method handles the actual file movement operation, including:
        - Resolving relative paths to absolute paths
        - Validating that the source file exists
        - Creating destination category folders if they don't exist
        - Handling file conflicts based on the overwrite parameter
        - Executing the file move operation safely
        - Comprehensive logging of operations and errors

        The destination is determined by:
        1. Using the provided category parameter if supplied
        2. Otherwise, automatically determining the category using categorize_file()

        The destination structure follows the pattern:
          {source_folder}/{category}/{filename}

        Args:
            file_path (str or Path): Path to the file to move. Can be absolute or relative.
                                    If relative, it's resolved relative to source_folder.
            category (str, optional): Destination category subfolder name. If None, the
                                    category is automatically determined from the file extension.
                                    Defaults to None.
            overwrite (bool, optional): If True, overwrite any existing files at the destination.
                                       If False, raise FileExistsError when destination exists.
                                       Defaults to False.

        Raises:
            FileExistsError: If the destination file already exists and overwrite is False.
            Various exceptions: From filesystem operations like permission errors,
                              disk full errors, etc. These are logged and re-raised.

        Returns:
            None: The method returns None on success. Exceptions are raised on failure.

        Note:
            - This method always creates the destination category folder if it doesn't exist
            - The operation is logged at the info level when successful
            - Errors are logged with traceback information for debugging
            - The method ensures absolute paths are used for all file operations

        Example:
            >>> mover = FileMover('/downloads', {})
            >>> # Move a file to a specific category
            >>> mover.move_file('/downloads/report.pdf', 'work_documents')
            >>> # Move a file using automatic categorization
            >>> mover.move_file('/downloads/image.jpg')  # Will go to 'images' folder
        """
        # Convert file_path to Path object for consistent handling
        source_path = Path(file_path)
        # If a bare filename is provided, resolve it under the configured source folder
        if not source_path.is_absolute():
            source_path = Path(self.source_folder) / source_path

        if not source_path.exists() or not source_path.is_file():
            if self.logger:
                self.logger.warning(
                    f"File does not exist or is not a file: {source_path}"
                )
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
                    self.logger.error(
                        f"Destination already exists and overwrite is False: {destination_path}"
                    )
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
        Orchestrate the complete file organization process for the source folder.

        This is the main entry point for file organization. It performs a comprehensive
        workflow including directory scanning, file categorization, and either preview
        or actual file movement operations.

        The organization process:
        1. Logs the start of the organization operation
        2. Recursively scans the source folder for all files
        3. For each file found:
           a. Determines the appropriate category using categorize_file()
           b. Logs the categorization decision
           c. Either shows what would happen (dry-run) or performs the move
        4. Handles errors gracefully, logging them but continuing with other files
        5. Reports completion status

        File Movement Structure:
        Files are moved into category subdirectories within the source folder:
          Before: /source/document.pdf, /source/image.jpg
          After:  /source/documents/document.pdf, /source/images/image.jpg

        Args:
            dry_run (bool, optional): If True, performs a simulation showing what
                                     files would be moved without actually moving them.
                                     Useful for previewing the organization before committing.
                                     Defaults to False.
            overwrite (bool, optional): If True, overwrites existing files at destinations.
                                       If False, files that would conflict with existing
                                       files are skipped (in dry-run) or raise FileExistsError
                                       (in actual operation). Defaults to False.

        Returns:
            None: This method doesn't return a value. Success/failure is communicated
                 through logging and raised exceptions.

        Raises:
            Various exceptions: Individual file operations may raise exceptions (logged
                              but don't stop the overall process). The method continues
                              processing other files even if some operations fail.

        Note:
            - The method is resilient to individual file errors and will continue
              processing remaining files even if some operations fail
            - All operations are logged at appropriate levels (info for success, error for failures)
            - In dry-run mode, existing file conflicts are identified and reported
            - Category folders are created automatically as needed during the process

        Example:
            >>> mover = FileMover('/downloads', {})
            >>> # Preview what would happen
            >>> mover.organize(dry_run=True)
            >>> # Actually organize files
            >>> mover.organize()
            >>> # Organize with overwrite enabled
            >>> mover.organize(overwrite=True)
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
                        self.logger.info(
                            f"[DRY RUN] Would move '{file_path}' -> '{destination_path}'"
                        )
                else:
                    # Actually move the file
                    self.move_file(file_path, category, overwrite=overwrite)
            except Exception as exc:
                if self.logger:
                    self.logger.error(
                        f"Failed to organize '{file_path}': {exc}", exc_info=True
                    )

        if self.logger:
            if dry_run:
                self.logger.info("Dry run complete - no files were moved")
            else:
                self.logger.info("Organization complete")


def move_file(
    source: str, destination: str, overwrite: bool = False, max_retries: int = 3
) -> None:
    """
    Move a file from source to destination.

    Args:
        source: Path to the source file.
        destination: Full destination path (including filename).
        overwrite: If True and destination exists, replace it. If False, raise FileExistsError.
        max_retries: Maximum number of retry attempts for file lock errors. Defaults to 3.

    Raises:
        FileNotFoundError: If the source file does not exist.
        FileExistsError: If the destination exists and overwrite is False.
        Exception: Propagates exceptions from the underlying filesystem operations.
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
            logger.error(
                f"Destination already exists and overwrite is False: {dest_path}"
            )
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
            logger.error(
                f"Failed to move {src_path} -> {dest_path}: {exc}", exc_info=True
            )
            raise
