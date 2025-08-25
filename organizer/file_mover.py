from pathlib import Path
import logging


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
        self.source_folder = Path(source_folder)
        self.dest_folders = dest_folders
        self.logger = logger or logging.getLogger(__name__)

    def move_file(self, file_path):
        """
        Move a single file to the appropriate destination folder
        """
        # TODO: implement file moving logic
        if self.logger:
            self.logger.info(f"Moving file: {file_path}")

    def organize(self):
        """
        Scan the source folder and organize all files
        """
        # TODO: implement scanning and moving logic
        if self.logger:
            self.logger.info(f"Organizing folder: {self.source_folder}")
