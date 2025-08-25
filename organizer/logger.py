import logging
import os


def setup_logger(log_file="logs/organizer.log"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Optional: also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
