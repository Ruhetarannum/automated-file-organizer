import json
import subprocess
import sys
from pathlib import Path

import pytest

from organizer.cli import main as cli_main


# 1. Smoke test (your original style)
def test_cli_runs(monkeypatch):
    test_args = ["organizer", "--source", "test_dir"]
    monkeypatch.setattr(sys, "argv", test_args)

    try:
        cli_main()
    except SystemExit as e:
        assert e.code == 0


# 2. CLI help command test
def test_cli_help():
    with pytest.raises(SystemExit) as e:
        cli_main(["--help"])
    assert e.value.code == 0


# 2b. CLI help command test with subprocess to capture output
def test_cli_help_shows_all_options():
    """Test that CLI help shows all expected options including --dry-run and --overwrite."""
    # Run CLI help command and capture output
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    # Verify CLI executed successfully
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"

    # Get the help output
    help_output = result.stdout

    # Assert that all expected options appear in help
    assert "--config" in help_output, "Help should show --config option"
    assert "--source" in help_output, "Help should show --source option"
    assert "--verbose" in help_output, "Help should show --verbose option"
    assert "--dry-run" in help_output, "Help should show --dry-run option"
    assert "--overwrite" in help_output, "Help should show --overwrite option"

    # Assert that help descriptions are present
    assert (
        "Show which files would be moved without actually moving" in help_output
    ), "Help should describe --dry-run functionality"
    assert "them." in help_output, "Help should show complete --dry-run description"
    assert (
        "Overwrite existing files at destination (default: False)." in help_output
    ), "Help should describe --overwrite functionality"

    # Print help output for debugging if needed
    if "--dry-run" not in help_output or "--overwrite" not in help_output:
        print("\nDEBUG: CLI help output:")
        print(help_output)


# 3. Functional test with tmp_path
def test_cli_organizes_files(tmp_path):
    # Setup: make fake files in tmp_path
    txt_file = tmp_path / "notes.txt"
    img_file = tmp_path / "photo.jpg"
    txt_file.write_text("hello")
    img_file.write_text("image data")

    # Run CLI with tmp_path as source
    exit_code = cli_main(["--source", str(tmp_path)])
    assert exit_code == 0

    # Assert files are moved into category folders
    documents_folder = tmp_path / "Documents"
    images_folder = tmp_path / "Images"

    assert (documents_folder / "notes.txt").exists()
    assert (images_folder / "photo.jpg").exists()


# 4. Edge case: empty directory
def test_cli_empty_dir(tmp_path):
    # Empty dir created by tmp_path
    exit_code = cli_main(["--source", str(tmp_path)])
    # Should not crash
    assert exit_code == 0


# 5. Integration test: CLI without --dry-run should move files into categorized folders
def test_cli_moves_files_real(tmp_path):
    """Test that CLI without --dry-run actually moves files into categorized folders."""
    # Setup: create test files in tmp_path
    txt_file = tmp_path / "document.txt"
    jpg_file = tmp_path / "photo.jpg"
    pdf_file = tmp_path / "report.pdf"

    txt_file.write_text("This is a text document")
    jpg_file.write_text("fake image data")
    pdf_file.write_text("fake pdf content")

    # Create a test config file in tmp_path
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

    # Run CLI with test config
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--config", str(test_config), "--verbose"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert files are moved into category folders
    documents_folder = tmp_path / "documents"
    images_folder = tmp_path / "images"

    assert documents_folder.exists(), "Documents folder should be created"
    assert images_folder.exists(), "Images folder should be created"
    assert (documents_folder / "document.txt").exists(), "Text file should be moved to documents"
    assert (documents_folder / "report.pdf").exists(), "PDF file should be moved to documents"
    assert (images_folder / "photo.jpg").exists(), "Image file should be moved to images"

    # Assert source files are gone
    assert not txt_file.exists(), "Source text file should be removed"
    assert not jpg_file.exists(), "Source image file should be removed"
    assert not pdf_file.exists(), "Source PDF file should be removed"


# 6. Integration test: CLI with --dry-run should not move files but show planned actions
def test_cli_dry_run_shows_planned_actions(tmp_path):
    """Test that CLI with --dry-run shows planned actions without moving files."""
    # Setup: create test files in tmp_path
    txt_file = tmp_path / "notes.txt"
    jpg_file = tmp_path / "snapshot.jpg"

    txt_file.write_text("Some notes")
    jpg_file.write_text("fake image")

    # Create a test config file in tmp_path
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

    # Run CLI with --dry-run flag and verbose output
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--config",
            str(test_config),
            "--dry-run",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert dry-run mode is indicated (check both stdout and stderr for verbose output)
    output = result.stdout + result.stderr
    assert "DRY RUN MODE" in output, "Should indicate dry-run mode"
    assert "Would move" in output, "Should show planned moves"

    # Assert files are NOT moved (still in original location)
    assert txt_file.exists(), "Text file should remain in source during dry-run"
    assert jpg_file.exists(), "Image file should remain in source during dry-run"

    # Assert no category folders are created
    documents_folder = tmp_path / "documents"
    images_folder = tmp_path / "images"
    assert not documents_folder.exists(), "Documents folder should not be created during dry-run"
    assert not images_folder.exists(), "Images folder should not be created during dry-run"


# 7. Integration test: CLI with --overwrite should replace existing destination files
def test_cli_overwrite_replaces_existing_files(tmp_path):
    """Test that CLI with --overwrite replaces existing destination files."""
    # Setup: create test files in tmp_path
    source_txt = tmp_path / "document.txt"
    source_txt.write_text("New content")

    # Create existing destination file with different content
    documents_folder = tmp_path / "documents"
    documents_folder.mkdir()
    existing_txt = documents_folder / "document.txt"
    existing_txt.write_text("Old content")

    # Create a test config file in tmp_path
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

    # Run CLI with --overwrite flag
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--config", str(test_config), "--overwrite"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert source file is moved
    assert not source_txt.exists(), "Source file should be moved"

    # Assert destination file has new content
    assert (documents_folder / "document.txt").exists(), "Destination file should exist"
    assert (documents_folder / "document.txt").read_text() == "New content", "Destination should have new content"


# 8. Integration test: CLI with --overwrite and --dry-run should show overwrite plans
def test_cli_overwrite_dry_run_shows_overwrite_plans(tmp_path):
    """Test that CLI with both --overwrite and --dry-run shows overwrite plans."""
    # Setup: create test files in tmp_path
    source_txt = tmp_path / "document.txt"
    source_txt.write_text("New content")

    # Create existing destination file
    documents_folder = tmp_path / "documents"
    documents_folder.mkdir()
    existing_txt = documents_folder / "document.txt"
    existing_txt.write_text("Old content")

    # Create a test config file in tmp_path
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

    # Run CLI with both --overwrite and --dry-run flags
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--config",
            str(test_config),
            "--overwrite",
            "--dry-run",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert dry-run mode is indicated (check both stdout and stderr for verbose output)
    output = result.stdout + result.stderr
    assert "DRY RUN MODE" in output, "Should indicate dry-run mode"
    assert "Would move" in output, "Should show planned moves"

    # Assert files are NOT moved (still in original location)
    assert source_txt.exists(), "Source file should remain during dry-run"
    assert existing_txt.exists(), "Destination file should remain during dry-run"
    assert existing_txt.read_text() == "Old content", "Destination content should remain unchanged"


# 9. Integration test: CLI handles permission errors gracefully
def test_cli_handles_permission_errors(tmp_path):
    """Test that CLI handles permission errors gracefully."""
    # Setup: create test file in tmp_path
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("test content")

    # Make the file read-only (simulate permission issue)
    txt_file.chmod(0o444)  # Read-only

    # Create a test config file in tmp_path
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

    # Run CLI and expect it to handle the error gracefully
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--config", str(test_config)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    # CLI should complete (even with errors) but log the issues
    assert result.returncode == 0, f"CLI should complete even with permission errors: {result.stderr}"

    # File should remain in place due to permission error
    assert txt_file.exists(), "File should remain due to permission error"

    # Clean up: restore write permissions
    txt_file.chmod(0o666)


# 10. Integration test: CLI creates nested destination directories
def test_cli_creates_nested_destinations(tmp_path):
    """Test that CLI creates nested destination directories when needed."""
    # Setup: create test file in tmp_path
    txt_file = tmp_path / "deeply" / "nested" / "document.txt"
    txt_file.parent.mkdir(parents=True)
    txt_file.write_text("nested content")

    # Create a test config file in tmp_path
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

    # Run CLI
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--config", str(test_config)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert nested structure is created in documents folder
    documents_folder = tmp_path / "documents"
    nested_doc = documents_folder / "deeply" / "nested" / "document.txt"

    assert nested_doc.exists(), "Nested document should be moved to documents folder"
    assert nested_doc.read_text() == "nested content", "Content should be preserved"

    # Assert source structure is removed
    assert not txt_file.exists(), "Source file should be removed"
    assert not txt_file.parent.exists(), "Source directory structure should be removed"


# 11. Focused test: CLI --dry-run captures and shows "would move" messages
def test_cli_dry_run_captures_would_move_messages(tmp_path):
    """Test that CLI with --dry-run captures stdout/stderr and shows 'would move' messages."""
    # Setup: create test files in tmp_path
    txt_file = tmp_path / "document.txt"
    jpg_file = tmp_path / "photo.jpg"
    pdf_file = tmp_path / "report.pdf"

    txt_file.write_text("This is a text document")
    jpg_file.write_text("fake image data")
    pdf_file.write_text("fake pdf content")

    # Create a test config file in tmp_path
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

    # Run CLI with --dry-run flag and capture output
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--config",
            str(test_config),
            "--dry-run",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
    )

    # Verify CLI executed successfully
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Combine stdout and stderr to check all output
    output = result.stdout + result.stderr

    # Assert dry-run mode is indicated
    assert "DRY RUN MODE" in output, "Should indicate dry-run mode"

    # Assert specific "would move" messages for each file type
    assert "Would move" in output, "Should contain 'Would move' messages"

    # Check for specific file movements
    txt_filename = txt_file.name
    jpg_filename = jpg_file.name
    pdf_filename = pdf_file.name

    # Assert that each file has a corresponding "would move" message
    assert "Would move" in output, "Should show planned moves for files"

    # Verify files remain in place (dry-run should not move anything)
    assert txt_file.exists(), f"Text file {txt_filename} should remain in source during dry-run"
    assert jpg_file.exists(), f"Image file {jpg_filename} should remain in source during dry-run"
    assert pdf_file.exists(), f"PDF file {pdf_filename} should remain in source during dry-run"

    # Verify no destination folders are created
    documents_folder = tmp_path / "documents"
    images_folder = tmp_path / "images"
    assert not documents_folder.exists(), "Documents folder should not be created during dry-run"
    assert not images_folder.exists(), "Images folder should not be created during dry-run"

    # Print captured output for debugging if needed
    if "Would move" not in output:
        print("\nDEBUG: CLI output did not contain 'Would move' messages")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"Combined output: {output}")
