"""Metacognition journal (F-68): data-driven weekly prompt, private entries."""
import unittest

from groundwork import db as dbmod
from groundwork import journal as journalmod

from test_web import handler_for, make_module


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("journal mod")
        dbmod.init_db(self.db)

    def test_prompt_falls_back_without_data(self):
        self.assertIn("surprised you", journalmod.week_prompt(self.db))

    def test_save_lists_and_renders(self):
        self.assertIn("error", journalmod.save(self.db, "   "))
        out = journalmod.save(self.db, "I misjudged the loop bound.")
        self.assertNotIn("error", out)
        page = journalmod.page_html(self.db)
        self.assertIn("id='journal'", page)
        self.assertIn("I misjudged the loop bound.", page)

    def test_journal_route_renders(self):
        self.assertIn("id='journal'", handler_for(self.db).journal_html())


if __name__ == "__main__":
    unittest.main()
