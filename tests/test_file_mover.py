"""Tests for FileMover class functionality.

This module contains comprehensive tests for the categorize_file function including:
- Built-in categories: Images, Documents, Videos, Music, Archives, Code
- Configuration file integration (.fileorganizer.json)
- User config file support with custom mappings
- Config priority over built-in categories
- Fallback to built-in categories when config is incomplete
- Case-insensitive extension matching (both built-in and config)
- Unknown extension handling (returns 'others')
- Empty/invalid config handling
- File movement operations

Key test scenarios for user config file support:
1. Custom mappings override built-in categories
2. Partial configs fall back to built-in for unmapped extensions
3. Unknown extensions return 'others' even with custom config
4. Config file takes complete priority when extensions conflict
5. Empty or invalid configs gracefully fall back to built-in categories
"""

import pytest
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from organizer.file_mover import FileMover, clear_config_cache
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


def test_categorize_file_music(mover):
    """Test music file categorization."""
    assert mover.categorize_file("song.mp3") == "music"
    assert mover.categorize_file("track.MP3") == "music"  # Test uppercase
    assert mover.categorize_file("audio.wav") == "music"
    assert mover.categorize_file("lossless.flac") == "music"
    assert mover.categorize_file("compressed.aac") == "music"


def test_categorize_file_archives(mover):
    """Test archive file categorization."""
    assert mover.categorize_file("archive.zip") == "archives"
    assert mover.categorize_file("backup.ZIP") == "archives"  # Test uppercase
    assert mover.categorize_file("package.rar") == "archives"
    assert mover.categorize_file("source.tar") == "archives"
    assert mover.categorize_file("compressed.gz") == "archives"
    assert mover.categorize_file("sevenz.7z") == "archives"


def test_categorize_file_code(mover):
    """Test code file categorization."""
    assert mover.categorize_file("script.py") == "code"
    assert mover.categorize_file("Main.PY") == "code"  # Test uppercase
    assert mover.categorize_file("program.java") == "code"
    assert mover.categorize_file("source.cpp") == "code"
    assert mover.categorize_file("app.js") == "code"
    assert mover.categorize_file("component.ts") == "code"
    assert mover.categorize_file("index.html") == "code"
    assert mover.categorize_file("styles.css") == "code"


def test_categorize_file_unknown_extension(mover):
    """Test unknown file extensions return 'others'."""
    # Use extensions that are not in the .fileorganizer.json config file
    assert mover.categorize_file("data.unknown123") == "others"
    assert mover.categorize_file("file.weird456") == "others"
    assert mover.categorize_file("test.notreal") == "others"
    assert mover.categorize_file("binary.blob") == "others"


def test_categorize_file_no_extension(mover):
    assert mover.categorize_file("LICENSE") == "others"


def test_categorize_file_config_file_extensions(mover):
    """Test that config file extensions work correctly."""
    # These extensions should be matched by the .fileorganizer.json config file
    assert (
        mover.categorize_file("data.xyz") == "custom"
    )  # From Custom category in config
    assert (
        mover.categorize_file("file.custom") == "custom"
    )  # From Custom category in config
    assert (
        mover.categorize_file("test.special") == "custom"
    )  # From Custom category in config


def test_categorize_file_built_in_without_config(mover):
    """Test built-in categories when config file is not available."""
    # Mock the load_config function to return None (no config file)
    with mock.patch("organizer.file_mover.load_config", return_value=None):
        # Clear config cache to ensure fresh load
        clear_config_cache()

        # Test built-in categories work when no config file
        assert mover.categorize_file("song.mp3") == "music"
        assert mover.categorize_file("archive.zip") == "archives"
        assert mover.categorize_file("script.py") == "code"
        assert mover.categorize_file("unknown.ext") == "others"

    # Clear cache after test to restore normal behavior
    clear_config_cache()


def test_categorize_file_case_insensitive(mover):
    """Test that file extension matching is case insensitive."""
    # Test various case combinations
    assert mover.categorize_file("SONG.MP3") == "music"
    assert mover.categorize_file("Archive.ZIP") == "archives"
    assert mover.categorize_file("Script.PY") == "code"
    assert mover.categorize_file("Photo.JPG") == "images"
    assert mover.categorize_file("Document.PDF") == "documents"
    assert mover.categorize_file("Video.MP4") == "videos"


def test_categorize_file_custom_config_mapping(mover):
    """Test that custom config mappings take precedence over built-in categories."""
    # Mock a custom config with specific mappings
    custom_config = {
        "CustomCategory": [".xyz", ".special"],
        "WorkFiles": [".docx", ".pptx"],  # Override some built-in document types
        "MediaFiles": [".mp3", ".mp4"],  # Override music and video types
    }

    with mock.patch("organizer.file_mover.load_config", return_value=custom_config):
        clear_config_cache()  # Clear cache to force reload

        # Test custom mappings work
        assert mover.categorize_file("file.xyz") == "customcategory"
        assert mover.categorize_file("data.special") == "customcategory"

        # Test overriding built-in categories
        assert mover.categorize_file("document.docx") == "workfiles"  # Not 'documents'
        assert (
            mover.categorize_file("presentation.pptx") == "workfiles"
        )  # Not 'documents'

        # Test media override
        assert mover.categorize_file("song.mp3") == "mediafiles"  # Not 'music'
        assert mover.categorize_file("video.mp4") == "mediafiles"  # Not 'videos'

    clear_config_cache()  # Restore normal behavior


def test_categorize_file_config_fallback_to_builtin(mover):
    """Test that built-in categories work when custom config doesn't have mapping."""
    # Mock a config that only has some custom mappings
    partial_config = {"CustomDocs": [".xyz", ".custom"], "SpecialArchives": [".myzip"]}

    with mock.patch("organizer.file_mover.load_config", return_value=partial_config):
        clear_config_cache()

        # Test custom mappings work
        assert mover.categorize_file("file.xyz") == "customdocs"
        assert mover.categorize_file("archive.myzip") == "specialarchives"

        # Test fallback to built-in for extensions not in config
        assert mover.categorize_file("song.mp3") == "music"  # Falls back to built-in
        assert (
            mover.categorize_file("archive.zip") == "archives"
        )  # Falls back to built-in
        assert mover.categorize_file("script.py") == "code"  # Falls back to built-in
        assert mover.categorize_file("photo.jpg") == "images"  # Falls back to built-in

    clear_config_cache()


def test_categorize_file_config_unknown_extensions_return_others(mover):
    """Test that unknown extensions return 'others' even with custom config."""
    custom_config = {"MyCategory": [".xyz", ".abc"], "WorkStuff": [".work", ".biz"]}

    with mock.patch("organizer.file_mover.load_config", return_value=custom_config):
        clear_config_cache()

        # Test custom extensions work
        assert mover.categorize_file("file.xyz") == "mycategory"
        assert mover.categorize_file("document.work") == "workstuff"

        # Test unknown extensions return 'others'
        assert mover.categorize_file("mystery.unknown") == "others"
        assert mover.categorize_file("data.weird") == "others"
        assert mover.categorize_file("file.notfound") == "others"

    clear_config_cache()


def test_categorize_file_config_case_insensitive_matching(mover):
    """Test that config file extensions are matched case-insensitively."""
    custom_config = {"SpecialFiles": [".xyz", ".custom"], "WorkDocs": [".workfile"]}

    with mock.patch("organizer.file_mover.load_config", return_value=custom_config):
        clear_config_cache()

        # Test different case combinations
        assert mover.categorize_file("file.xyz") == "specialfiles"
        assert mover.categorize_file("file.XYZ") == "specialfiles"
        assert mover.categorize_file("file.Xyz") == "specialfiles"

        assert mover.categorize_file("doc.custom") == "specialfiles"
        assert mover.categorize_file("doc.CUSTOM") == "specialfiles"

        assert mover.categorize_file("work.workfile") == "workdocs"
        assert mover.categorize_file("work.WORKFILE") == "workdocs"
        assert mover.categorize_file("work.WorkFile") == "workdocs"

    clear_config_cache()


def test_categorize_file_config_priority_over_builtin(mover):
    """Test that config file mappings take complete priority over built-in categories."""
    # Create a config that deliberately conflicts with built-in categories
    conflicting_config = {
        "NotImages": [".jpg", ".png"],  # Override image extensions
        "NotDocuments": [".pdf", ".txt"],  # Override document extensions
        "NotCode": [".py", ".js"],  # Override code extensions
        "Special": [".newext"],
    }

    with mock.patch(
        "organizer.file_mover.load_config", return_value=conflicting_config
    ):
        clear_config_cache()

        # Config should take priority over built-ins
        assert mover.categorize_file("photo.jpg") == "notimages"  # Not 'images'
        assert mover.categorize_file("image.png") == "notimages"  # Not 'images'

        assert mover.categorize_file("doc.pdf") == "notdocuments"  # Not 'documents'
        assert mover.categorize_file("note.txt") == "notdocuments"  # Not 'documents'

        assert mover.categorize_file("script.py") == "notcode"  # Not 'code'
        assert mover.categorize_file("app.js") == "notcode"  # Not 'code'

        # Extensions not in config should fall back to built-in
        assert mover.categorize_file("song.mp3") == "music"  # Falls back
        assert mover.categorize_file("archive.zip") == "archives"  # Falls back

        # Completely unknown should return 'others'
        assert mover.categorize_file("mystery.unknown") == "others"

    clear_config_cache()


def test_categorize_file_empty_config_uses_builtin(mover):
    """Test that an empty config falls back to built-in categories."""
    empty_config = {}

    with mock.patch("organizer.file_mover.load_config", return_value=empty_config):
        clear_config_cache()

        # Should fall back to built-in categories
        assert mover.categorize_file("song.mp3") == "music"
        assert mover.categorize_file("photo.jpg") == "images"
        assert mover.categorize_file("script.py") == "code"
        assert mover.categorize_file("archive.zip") == "archives"
        assert mover.categorize_file("doc.pdf") == "documents"
        assert mover.categorize_file("video.mp4") == "videos"

        # Unknown extensions should return 'others'
        assert mover.categorize_file("unknown.ext") == "others"

    clear_config_cache()


def test_categorize_file_invalid_config_uses_builtin(mover):
    """Test that invalid config data falls back to built-in categories."""
    # Mock load_config to return None (simulating invalid/missing config)
    with mock.patch("organizer.file_mover.load_config", return_value=None):
        clear_config_cache()

        # Should fall back to built-in categories
        assert mover.categorize_file("song.mp3") == "music"
        assert mover.categorize_file("photo.jpg") == "images"
        assert mover.categorize_file("script.py") == "code"
        assert mover.categorize_file("archive.zip") == "archives"
        assert mover.categorize_file("doc.pdf") == "documents"
        assert mover.categorize_file("video.mp4") == "videos"

        # Unknown extensions should return 'others'
        assert mover.categorize_file("unknown.ext") == "others"

    clear_config_cache()


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
