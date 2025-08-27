import sys
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
