from organizer.file_mover import FileMover
from organizer.logger import setup_logger
import json
import os


def load_config(config_path="config/config.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"{config_path} not found!")
    with open(config_path, "r") as f:
        return json.load(f)


def main():
    config = load_config()
    logger = setup_logger()

    print("Starting file organization...")
    mover = FileMover(config["source_folder"], config["destination_folders"], logger)
    mover.organize()
    print("File organization complete.")
    logger.info("Setup complete")


if __name__ == "__main__":
    main()
