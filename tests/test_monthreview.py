"""Month in review (I-244): owned concepts, accuracy trend, effort."""
import unittest

from groundwork import history as histmod
from groundwork import monthreview as monthmod

from test_web import make_module


class MonthTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("month mod")
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)

    def test_section_reports_month(self):
        out = monthmod.section_html(self.db)
        self.assertIn("id='month'", out)
        self.assertIn("Accuracy trend", out)
        self.assertIn("owned", out)

    def test_empty_month_is_calm(self):
        import tempfile
        from groundwork import db as dbmod
        p = tempfile.mktemp(suffix=".db")
        dbmod.init_db(p)
        try:
            out = monthmod.section_html(p)
        finally:
            import os
            os.unlink(p)
        self.assertIn("id='month'", out)
        self.assertIn("No attempts", out)

    def test_history_page_carries_month(self):
        self.assertIn("id='month'", histmod.history_html(self.db))


if __name__ == "__main__":
    unittest.main()
