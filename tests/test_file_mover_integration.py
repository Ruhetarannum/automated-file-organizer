import logging

import pytest

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


def test_move_file_overwrite_false_raises_file_exists_error(tmp_path):
    """Test that overwrite=False raises FileExistsError if destination already exists."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    # Create source and destination files
    src.write_text("source content", encoding="utf-8")
    dst.write_text("existing content", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Destination already exists"):
        move_file(str(src), str(dst), overwrite=False)

    # Verify files remain unchanged
    assert src.exists()
    assert dst.exists()
    assert src.read_text(encoding="utf-8") == "source content"
    assert dst.read_text(encoding="utf-8") == "existing content"


def test_move_file_overwrite_true_replaces_destination(tmp_path):
    """Test that overwrite=True replaces destination contents."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    # Create source and destination files
    src.write_text("new content", encoding="utf-8")
    dst.write_text("old content", encoding="utf-8")

    move_file(str(src), str(dst), overwrite=True)

    # Verify source is moved and destination has new content
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == "new content"


def test_move_file_overwrite_true_creates_parent_directories(tmp_path):
    """Test that overwrite=True creates parent directories if they don't exist."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "nested" / "deep" / "dest.txt"

    src.write_text("content", encoding="utf-8")

    move_file(str(src), str(dst), overwrite=True)

    # Verify parent directories were created
    assert dst.parent.exists()
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == "content"


def test_move_file_permission_error_source_not_writable(tmp_path, monkeypatch):
    """Test that PermissionError is raised when source is not writable."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Mock os.access to simulate source file not being writable
    def mock_access(path, mode):
        if str(path) == str(src):
            return False  # Source not writable
        return True

    monkeypatch.setattr("os.access", mock_access)

    with pytest.raises(PermissionError):
        move_file(str(src), str(dst))


def test_move_file_permission_error_destination_not_writable(tmp_path, monkeypatch):
    """Test that PermissionError is raised when destination is not writable."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Mock os.access to simulate destination directory not being writable
    def mock_access(path, mode):
        if str(path) == str(dst.parent):
            return False  # Destination parent not writable
        return True

    monkeypatch.setattr("os.access", mock_access)

    with pytest.raises(PermissionError):
        move_file(str(src), str(dst))


def test_move_file_retry_logic_attempts_retries_on_permission_error(tmp_path, monkeypatch):
    """Test that retry logic is attempted by patching time.sleep and simulating PermissionError."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Track sleep calls and shutil.move calls
    sleep_calls = []
    move_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    def mock_move(src_path, dst_path):
        move_calls.append((src_path, dst_path))
        # Raise PermissionError on first 2 calls, succeed on 3rd
        if len(move_calls) <= 2:
            raise PermissionError("File is locked")
        # Success on 3rd attempt

    monkeypatch.setattr("time.sleep", mock_sleep)
    monkeypatch.setattr("shutil.move", mock_move)

    # Should succeed after 2 retries
    move_file(str(src), str(dst), max_retries=3)

    # Verify retry behavior
    assert len(move_calls) == 3  # Initial + 2 retries
    assert len(sleep_calls) == 2  # 2 sleep calls between retries
    assert sleep_calls == [0.5, 0.5]  # 0.5 second delays


def test_move_file_retry_logic_fails_after_max_retries(tmp_path, monkeypatch):
    """Test that retry logic fails and logs error after max retries."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Track sleep calls and shutil.move calls
    sleep_calls = []
    move_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    def mock_move(src_path, dst_path):
        move_calls.append((src_path, dst_path))
        # Always raise PermissionError
        raise PermissionError("File is locked")

    monkeypatch.setattr("time.sleep", mock_sleep)
    monkeypatch.setattr("shutil.move", mock_move)

    # Should fail after max retries
    with pytest.raises(PermissionError, match="File is locked"):
        move_file(str(src), str(dst), max_retries=2)

    # Verify retry behavior
    assert len(move_calls) == 3  # Initial + 2 retries
    assert len(sleep_calls) == 2  # 2 sleep calls between retries
    assert sleep_calls == [0.5, 0.5]  # 0.5 second delays


def test_move_file_retry_logic_custom_max_retries(tmp_path, monkeypatch):
    """Test that custom max_retries parameter works correctly."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Track sleep calls and shutil.move calls
    sleep_calls = []
    move_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    def mock_move(src_path, dst_path):
        move_calls.append((src_path, dst_path))
        # Raise PermissionError on first call, succeed on 2nd
        if len(move_calls) <= 1:
            raise PermissionError("File is locked")
        # Success on 2nd attempt

    monkeypatch.setattr("time.sleep", mock_sleep)
    monkeypatch.setattr("shutil.move", mock_move)

    # Should succeed after 1 retry with max_retries=1
    move_file(str(src), str(dst), max_retries=1)

    # Verify retry behavior
    assert len(move_calls) == 2  # Initial + 1 retry
    assert len(sleep_calls) == 1  # 1 sleep call between retries
    assert sleep_calls == [0.5]  # 0.5 second delay


def test_move_file_retry_logic_no_retries_on_other_exceptions(tmp_path, monkeypatch):
    """Test that retry logic only applies to PermissionError, not other exceptions."""
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"

    src.write_text("content", encoding="utf-8")

    # Track sleep calls and shutil.move calls
    sleep_calls = []
    move_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    def mock_move(src_path, dst_path):
        move_calls.append((src_path, dst_path))
        # Raise OSError (not PermissionError)
        raise OSError("Some other error")

    monkeypatch.setattr("time.sleep", mock_sleep)
    monkeypatch.setattr("shutil.move", mock_move)

    # Should fail immediately without retries
    with pytest.raises(OSError, match="Some other error"):
        move_file(str(src), str(dst), max_retries=3)

    # Verify no retry behavior for non-PermissionError
    assert len(move_calls) == 1  # Only initial attempt
    assert len(sleep_calls) == 0  # No sleep calls
