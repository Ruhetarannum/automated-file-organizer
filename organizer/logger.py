import logging
import os


def setup_logger(log_file="logs/organizer.log", to_console=True):
    # Ensure logs folder exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called again
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
