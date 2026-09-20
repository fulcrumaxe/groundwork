"""File-map mini-view (I-128)."""
import unittest

from groundwork import filemap as fmmod


class FileMapTest(unittest.TestCase):
    def test_breadcrumb_and_tree(self):
        body = fmmod.file_map(["a/b.py", "a/c.py"], "a/b.py")
        self.assertIn("id='filemap'", body)
        self.assertIn("b.py", body)
        self.assertIn("<strong>", body)

    def test_empty(self):
        body = fmmod.file_map([], "")
        self.assertIn("id='filemap'", body)


if __name__ == "__main__":
    unittest.main()
