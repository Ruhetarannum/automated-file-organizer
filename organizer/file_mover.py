from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)


class FileMover:
    def __init__(self, source_folder, dest_folders: dict[str, str], logger=None):
        """
        Initialize the FileMover.

        Args:
            source_folder: path to the folder to organize
            dest_folders (dict[str, str]): A mapping of file extensions to destination folder names.
                Example: {".txt": "Documents", ".jpg": "Images"}
            logger (optional): Custom logger instance. Defaults to None.
        """
        # Store as raw value to keep compatibility with tests expecting a string
        self.source_folder = source_folder
        self.dest_folders = dest_folders
        self.logger = logger or logging.getLogger(__name__)

    def scan_directory(self, directory_path=None):
        """
        Scan a directory and return a list of absolute file paths without modifying them.

        Args:
            directory_path: Optional path to scan. Defaults to the instance's source folder.

        Returns:
            list[str]: Absolute paths to all files found (recursively).
        """
        base_path = Path(directory_path or self.source_folder)
        try:
            base_path = base_path.resolve()
        except Exception:
            # If resolution fails, proceed with the given path
            pass

        if not base_path.exists() or not base_path.is_dir():
            if self.logger:
                self.logger.warning(
                    f"Directory does not exist or is not a directory: {base_path}"
                )
            return []

        files = []
        for path in base_path.rglob("*"):
            if path.is_file():
                try:
                    files.append(str(path.resolve()))
                except Exception:
                    # Fallback to string representation if resolve fails
                    files.append(str(path))

        if self.logger:
            self.logger.info(f"Scanned {base_path}: found {len(files)} files")

        return files

    def categorize_file(self, file_path):
        """
        Return a category name based on the file extension.

        Categories: images, documents, videos, others.
        """
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
        }

        suffix = Path(file_path).suffix.lower()
        return extension_to_category.get(suffix, "others")

    def move_file(self, file_path, category=None):
        """
        Move a single file to the appropriate destination folder.

        Args:
            file_path: Path to the file to move.
            category: Destination category (subfolder name). If None, derive from extension.
        """
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

    def organize(self):
        """
        Scan the source folder and organize all files
        """
        if self.logger:
            self.logger.info(f"Organizing folder: {self.source_folder}")

        files = self.scan_directory(self.source_folder)

        for file_path in files:
            try:
                category = self.categorize_file(file_path)
                if self.logger:
                    self.logger.info(f"Categorized '{file_path}' as '{category}'")
                self.move_file(file_path, category)
            except Exception as exc:
                if self.logger:
                    self.logger.error(
                        f"Failed to organize '{file_path}': {exc}", exc_info=True
                    )

        if self.logger:
            self.logger.info("Organization complete")


def move_file(source: str, destination: str, overwrite: bool = False) -> None:
    """
    Move a file from source to destination.

    Args:
        source: Path to the source file.
        destination: Full destination path (including filename).
        overwrite: If True and destination exists, replace it. If False, raise FileExistsError.

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
        # Overwrite behavior: remove existing file or directory
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

    try:
        shutil.move(str(src_path), str(dest_path))
        logger.info(f"moved {src_path} -> {dest_path}")
    except Exception as exc:
        logger.error(f"Failed to move {src_path} -> {dest_path}: {exc}", exc_info=True)
        raise
