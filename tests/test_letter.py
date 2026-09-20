"""Weekly letter to self (F-106): honest prose from real numbers."""
import unittest

from groundwork import letter as lettermod
from groundwork import status as statusmod

from test_web import make_module


class LetterTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("letter mod")

    def test_quiet_week_is_kind(self):
        body = lettermod.draft(self.db)
        self.assertIn("not failure", body)

    def test_active_week_reports_numbers(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        body = lettermod.draft(self.db)
        self.assertIn("1 attempts", body)
        self.assertIn("Next:", body)
        self.assertNotIn("streak", body.lower())

    def test_status_page_carries_letter(self):
        self.assertIn("status-letter", statusmod.page_html(self.db))


if __name__ == "__main__":
    unittest.main()
