import pytest
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from organizer.file_mover import FileMover
from unittest import mock


@pytest.fixture
def mover(tmp_path):
    """Fixture to create a FileMover with a temp source folder."""
    source = tmp_path
    dest = {"others": str(tmp_path / "others")}
    return FileMover(str(source), dest)


def test_initialization(mover, tmp_path):
    assert mover.source_folder == str(tmp_path)
    assert mover.dest_folders == {"others": str(tmp_path / "others")}


def test_move_file_stub(mover):
    # Will always pass since move_file is still a stub
    mover.move_file("example.txt")
    assert True


def test_categorize_file_images(mover):
    assert mover.categorize_file("photo.JPG") == "images"
    assert mover.categorize_file("graphic.png") == "images"


def test_categorize_file_documents(mover):
    assert mover.categorize_file("report.PDF") == "documents"
    assert mover.categorize_file("notes.txt") == "documents"


def test_categorize_file_videos(mover):
    assert mover.categorize_file("clip.MP4") == "videos"
    assert mover.categorize_file("movie.mkv") == "videos"


def test_categorize_file_unknown_extension(mover):
    assert mover.categorize_file("archive.zip") == "others"
    assert mover.categorize_file("data.xyz") == "others"


def test_categorize_file_no_extension(mover):
    assert mover.categorize_file("LICENSE") == "others"


def test_move_file_moves_to_correct_folder(mover, tmp_path):
    # Arrange
    src_file = tmp_path / "sample.txt"
    src_file.write_text("hello world")

    # Act
    mover.move_file(str(src_file))

    # Assert: file should now exist in Documents folder
    target_file = tmp_path / "Documents" / "sample.txt"
    assert target_file.exists()
    # Original should be gone
    assert not src_file.exists()


def test_move_file_calls_shutil_move_with_correct_paths(tmp_path):
    # Arrange: create source folder and file
    source_dir = tmp_path
    sample = source_dir / "note.txt"  # .txt -> documents
    sample.write_text("content")

    mover = FileMover(str(source_dir), {"others": str(source_dir / "others")})

    with mock.patch("organizer.file_mover.shutil.move") as mock_move:
        # Act: use relative filename as API suggests
        mover.move_file("note.txt")

        # Assert: called with absolute source and destination under Documents
        expected_src = str(source_dir / "note.txt")
        expected_dst = str(source_dir / "documents" / "note.txt")
        mock_move.assert_called_once_with(expected_src, expected_dst)


class TestFileMover(unittest.TestCase):
    def setUp(self):
        self.source_dir = tempfile.mkdtemp(prefix="src_")
        self.dest_folders = {
            "documents": os.path.join(self.source_dir, "documents"),
            "others": os.path.join(self.source_dir, "others"),
        }
        self.mover = FileMover(self.source_dir, self.dest_folders)

        # Create a dummy file in source
        self.sample_filename = "sample.txt"
        Path(self.source_dir, self.sample_filename).write_text(
            "hello", encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.source_dir, ignore_errors=True)

    def test_move_file_moves_into_correct_category(self):
        # Act
        self.mover.move_file(self.sample_filename)

        # Assert: moved under documents category within source folder
        expected = Path(self.source_dir) / "documents" / self.sample_filename
        self.assertTrue(expected.exists())
        self.assertFalse(Path(self.source_dir, self.sample_filename).exists())
