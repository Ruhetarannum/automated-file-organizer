import unittest

# import os
# import sys
from organizer.file_mover import FileMover


class TestFileMover(unittest.TestCase):
    def setUp(self):
        self.source = "test_source"
        self.dest = {"others": "test_dest"}
        self.mover = FileMover(self.source, self.dest)

    def test_initialization(self):
        self.assertEqual(self.mover.source_folder, self.source)
        self.assertEqual(self.mover.dest_folders, self.dest)

    def test_move_file_stub(self):
        # This test will pass as move_file is currently a stub
        self.mover.move_file("example.txt")
        self.assertTrue(True)

    def test_categorize_file_images(self):
        self.assertEqual(self.mover.categorize_file("photo.JPG"), "images")
        self.assertEqual(self.mover.categorize_file("graphic.png"), "images")

    def test_categorize_file_documents(self):
        self.assertEqual(self.mover.categorize_file("report.PDF"), "documents")
        self.assertEqual(self.mover.categorize_file("notes.txt"), "documents")

    def test_categorize_file_videos(self):
        self.assertEqual(self.mover.categorize_file("clip.MP4"), "videos")
        self.assertEqual(self.mover.categorize_file("movie.mkv"), "videos")

    def test_categorize_file_unknown_extension(self):
        self.assertEqual(self.mover.categorize_file("archive.zip"), "others")
        self.assertEqual(self.mover.categorize_file("data.xyz"), "others")

    def test_categorize_file_no_extension(self):
        self.assertEqual(self.mover.categorize_file("LICENSE"), "others")


if __name__ == "__main__":
    unittest.main()
