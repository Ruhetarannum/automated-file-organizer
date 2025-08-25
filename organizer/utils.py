import os


def ensure_folder_exists(folder_path):
    """
    Create folder if it does not exist
    """
    os.makedirs(folder_path, exist_ok=True)


def get_file_extension(file_name):
    """
    Return the file extension (without dot)
    """
    return os.path.splitext(file_name)[1][1:].lower()
