"""North-star dashboard (F-52): delayed accuracy, honestly footnoted."""
import unittest

from groundwork import db as dbmod
from groundwork import northstar as northstarmod
from groundwork import status as statusmod

from test_web import make_module


class NorthStarTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("north mod")
        dbmod.init_db(self.db)

    def test_empty_state_has_anchor(self):
        out = northstarmod.section_html(self.db)
        self.assertIn("id='status-northstar'", out)
        self.assertIn("No mature recalls yet", out)

    def test_mature_review_counts(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        con = dbmod.connect(self.db)
        try:
            con.execute("UPDATE cards SET stability=30 WHERE id=?",
                        (card["id"],))
            con.commit()
        finally:
            con.close()
        self.server.submit_review(card["id"], "5", 4)
        snap = northstarmod.snapshot(self.db)
        self.assertEqual(snap["mature_n"], 1)
        self.assertEqual(snap["delayed_acc"], 1.0)
        self.assertIn("100%", northstarmod.section_html(self.db))

    def test_status_page_carries_section(self):
        self.assertIn("status-northstar", statusmod.page_html(self.db))


if __name__ == "__main__":
    unittest.main()
