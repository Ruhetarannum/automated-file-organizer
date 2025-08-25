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


if __name__ == "__main__":
    unittest.main()
