"""Personal bests (F-101): strongest memory, most practiced, sharpest."""
import unittest

from groundwork import bests as bestsmod
from groundwork import history as histmod

from test_web import make_module


class BestsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("bests mod")

    def test_empty_bests_have_anchor(self):
        out = bestsmod.section_html(self.db)
        self.assertIn("id='bests'", out)
        self.assertIn("Strongest memory:", out)

    def test_reviewed_bests_report(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        b = bestsmod.bests(self.db)
        self.assertIsNotNone(b["strong"])
        self.assertIsNotNone(b["practiced"])
        out = bestsmod.section_html(self.db)
        self.assertIn("Most practiced:", out)

    def test_history_carries_bests(self):
        self.assertIn("id='bests'", histmod.history_html(self.db))


if __name__ == "__main__":
    unittest.main()
