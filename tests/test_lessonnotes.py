"""Private lesson notes box (I-118)."""
import unittest

from groundwork import lessonnotes as lnmod


class NotesBoxTest(unittest.TestCase):
    def test_box_with_key(self):
        body = lnmod.notes_box("lesson-add")
        self.assertIn("id='lessonnotes'", body)
        self.assertIn("data-notes-for='lesson-add'", body)
        self.assertIn("localStorage", body)

    def test_blank_key_falls_back(self):
        body = lnmod.notes_box("")
        self.assertIn("data-notes-for='lesson'", body)


if __name__ == "__main__":
    unittest.main()
