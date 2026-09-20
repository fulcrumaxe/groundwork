"""Serendipity cards (F-137): adjacent concepts, labeled bonus."""
import unittest

from groundwork import serendipity as sermod

from test_web import handler_for, make_module


class SerendipityTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("ser mod")

    def test_picks_adjacent_non_due(self):
        cand = sermod.pick(self.db)
        out = sermod.section_html(self.db)
        self.assertIn("id='serendipity'", out)
        if cand is None:
            self.assertIn("whole neighborhood", out)
        else:
            self.assertIn("Bonus, not duty", out)
            self.assertIn("#lesson-", out)

    def test_due_page_carries_section(self):
        self.assertIn("id='serendipity'", handler_for(self.db).due_html())


if __name__ == "__main__":
    unittest.main()
