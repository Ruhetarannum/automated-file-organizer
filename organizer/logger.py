import logging
import os
import types


def setup_logger(log_file="logs/organizer.log"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    # Ensure traceback is included on error logs by default
    def error_with_trace(self, msg, *args, **kwargs):
        if "exc_info" not in kwargs:
            kwargs["exc_info"] = True
        return logging.Logger.error(self, msg, *args, **kwargs)

    logger.error = types.MethodType(error_with_trace, logger)

    return logger
