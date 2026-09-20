"""Grade disputes: file, list, resolve (I-193)."""
import unittest

from groundwork import disputes as dismod

from test_web import handler_for, make_module


class DisputeFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("dispute mod")
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.cid = card["id"]
        self.h = handler_for(self.db)

    def test_open_list_resolve(self):
        filed = dismod.open_dispute(self.db, self.cid, "reference is wrong")
        self.assertEqual(filed["status"], "open")
        open_rows = dismod.list_disputes(self.db)
        self.assertEqual(len(open_rows), 1)
        self.assertEqual(open_rows[0]["reason"], "reference is wrong")
        out = dismod.resolve_dispute(self.db, filed["dispute_id"], "accepted")
        self.assertEqual(out["status"], "accepted")
        self.assertEqual(dismod.list_disputes(self.db), [])
        done = dismod.list_disputes(self.db, "accepted")
        self.assertEqual(len(done), 1)

    def test_open_validates_input(self):
        self.assertIn("error", dismod.open_dispute(self.db, "nope", "why"))
        self.assertIn("error", dismod.open_dispute(self.db, self.cid, "  "))

    def test_resolve_validates_verdict(self):
        filed = dismod.open_dispute(self.db, self.cid, "why")
        self.assertIn("error", dismod.resolve_dispute(
            self.db, filed["dispute_id"], "maybe"))
        self.assertIn("error", dismod.resolve_dispute(self.db, 9999, "accepted"))

    def test_card_offers_dispute_form(self):
        body = self.h.due_html()
        self.assertIn("Dispute this grade", body)
        self.assertIn("/dispute", body)

    def test_status_shows_queue(self):
        dismod.open_dispute(self.db, self.cid, "wrong ref")
        body = self.h.status_html()
        self.assertIn("id='status-disputes'", body)
        self.assertIn("wrong ref", body)
        self.assertIn("/resolve", body)


if __name__ == "__main__":
    unittest.main()
