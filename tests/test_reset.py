"""Module reset: wipe progress behind a confirm page (I-236, I-36)."""
import unittest

from groundwork import db as dbmod
from groundwork import reset as resetmod

from test_web import handler_for, make_module


class ResetModuleTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("reset mod")
        self.mid = self.out["module_id"]
        self.h = handler_for(self.db)
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)

    def _counts(self):
        con = dbmod.connect(self.db)
        try:
            n_reviews = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            mastery = con.execute(
                "SELECT SUM(mastery) FROM concepts WHERE module_id=?",
                (self.mid,)).fetchone()[0]
        finally:
            con.close()
        return n_reviews, mastery

    def test_reset_wipes_progress_not_content(self):
        before = self._counts()
        self.assertGreater(before[0], 0)
        out = resetmod.reset_module(self.db, self.mid)
        self.assertGreater(out["reviews_deleted"], 0)
        self.assertGreater(out["cards_reset"], 0)
        after = self._counts()
        self.assertEqual(after[0], 0)
        self.assertEqual(after[1], 0.0)
        con = dbmod.connect(self.db)
        try:
            n_cards = con.execute(
                "SELECT COUNT(*) FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?", (self.mid,)).fetchone()[0]
            self.assertGreater(n_cards, 0)
        finally:
            con.close()

    def test_reset_unknown_module_errors(self):
        self.assertIn("error", resetmod.reset_module(self.db, "nope"))

    def test_module_page_links_reset_and_confirm_exists(self):
        body = self.h.module_html(self.mid)
        self.assertIn("id='reset'", body)
        self.assertIn(f"/modules/{self.mid}/reset", body)
        confirm = resetmod.confirm_html(self.mid, "reset mod")
        self.assertIn("id='reset-confirm'", confirm)
        self.assertIn(f"/modules/{self.mid}/reset", confirm)


if __name__ == "__main__":
    unittest.main()
