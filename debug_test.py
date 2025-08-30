import subprocess
import sys
import json
import shutil
from pathlib import Path

# Create a temporary directory structure
tmp_path = Path("debug_test_dir")
tmp_path.mkdir(exist_ok=True)

# Create test files
source_txt = tmp_path / "document.txt"
source_txt.write_text("New content")

# Create existing destination file
documents_folder = tmp_path / "documents"
documents_folder.mkdir()
existing_txt = documents_folder / "document.txt"
existing_txt.write_text("Old content")

# Create test config
test_config = tmp_path / "test_config.json"
config_data = {
    "source_folder": str(tmp_path),
    "destination_folders": {
        "images": str(tmp_path / "images"),
        "documents": str(tmp_path / "documents"),
        "videos": str(tmp_path / "videos"),
        "others": str(tmp_path / "others"),
    },
}
test_config.write_text(json.dumps(config_data, indent=4))

print("Before CLI:")
print(f"Source file exists: {source_txt.exists()}")
print(f"Source content: {source_txt.read_text()}")
print(f"Destination file exists: {existing_txt.exists()}")
print(f"Destination content: {existing_txt.read_text()}")

# Run CLI with --overwrite flag
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "cli.main",
        "--config",
        str(test_config),
        "--overwrite",
        "--verbose",
    ],
    capture_output=True,
    text=True,
    cwd=Path(__file__).parent,
)

print(f"\nCLI return code: {result.returncode}")
print(f"CLI stdout: {result.stdout}")
print(f"CLI stderr: {result.stderr}")

print("\nAfter CLI:")
print(f"Source file exists: {source_txt.exists()}")
if source_txt.exists():
    print(f"Source content: {source_txt.read_text()}")
print(f"Destination file exists: {existing_txt.exists()}")
if existing_txt.exists():
    print(f"Destination content: {existing_txt.read_text()}")

# Clean up
shutil.rmtree(tmp_path)
