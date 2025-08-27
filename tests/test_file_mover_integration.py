import pytest
import logging
from organizer.file_mover import FileMover, move_file


def test_move_file_moves_and_preserves_contents(tmp_path):
    source_dir = tmp_path
    mover = FileMover(str(source_dir), {"others": str(source_dir / "others")})

    src = source_dir / "report.txt"
    original = "hello docs"
    src.write_text(original, encoding="utf-8")

    mover.move_file("report.txt")

    dest = source_dir / "documents" / "report.txt"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == original


def test_move_file_creates_missing_destination_directories(tmp_path):
    source_dir = tmp_path
    mover = FileMover(str(source_dir), {"others": str(source_dir / "others")})

    # Ensure documents directory does not exist beforehand
    documents_dir = source_dir / "documents"
    assert not documents_dir.exists()

    (source_dir / "notes.txt").write_text("x", encoding="utf-8")
    mover.move_file("notes.txt")

    # Should be created and contain the file
    assert (documents_dir / "notes.txt").exists()


def test_move_file_missing_source_current_behavior_no_raise(tmp_path):
    source_dir = tmp_path
    mover = FileMover(str(source_dir), {"others": str(source_dir / "others")})

    # Current implementation logs a warning and returns without raising
    mover.move_file("missing.txt")
    assert not (source_dir / "documents" / "missing.txt").exists()


# The following test documents an alternative desired behavior.
# Enable if/when move_file is updated to raise on missing sources.


def test_move_file_raises_when_source_missing(tmp_path):
    source_dir = tmp_path
    mover = FileMover(str(source_dir), {"others": str(source_dir / "others")})
    with pytest.raises(FileNotFoundError):
        mover.move_file("missing.txt")


def test_move_file_logs_info_on_success(tmp_path, caplog):
    src = tmp_path / "log.txt"
    dst = tmp_path / "out" / "log.txt"
    src.write_text("x", encoding="utf-8")

    with caplog.at_level(logging.INFO, logger="organizer.file_mover"):
        move_file(str(src), str(dst))

    messages = [r.getMessage() for r in caplog.records]
    assert any("moved" in m and str(src) in m and str(dst) in m for m in messages)
