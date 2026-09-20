"""Undo last review (I-224): misclick recovery within 60 seconds."""
import unittest
from datetime import timedelta

from groundwork import db as dbmod
from groundwork import history as histmod
from groundwork import sched as schedmod
from groundwork import undo as undomod

from test_web import make_module


class UndoTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("undo mod")
        dbmod.init_db(self.db)
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.card_id = card["id"]
        con = dbmod.connect(self.db)
        try:
            self.before = dict(con.execute(
                "SELECT stability, difficulty, due, lapses FROM cards"
                " WHERE id=?", (self.card_id,)).fetchone())
        finally:
            con.close()
        self.server.submit_review(self.card_id, "5", 4)

    def test_snapshot_recorded(self):
        row = undomod.latest(self.db)
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row["prev_stability"], self.before["stability"])
        self.assertEqual(row["prev_due"], self.before["due"])

    def test_undo_restores_and_drops_row(self):
        out = undomod.undo(self.db)
        self.assertNotIn("error", out)
        con = dbmod.connect(self.db)
        try:
            after = dict(con.execute(
                "SELECT stability, difficulty, due, lapses FROM cards"
                " WHERE id=?", (self.card_id,)).fetchone())
            n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        finally:
            con.close()
        self.assertAlmostEqual(after["stability"], self.before["stability"])
        self.assertEqual(after["due"], self.before["due"])
        self.assertEqual(n, 0)
        self.assertIn("error", undomod.undo(self.db))

    def test_old_review_refuses(self):
        stale = (schedmod.utcnow() - timedelta(minutes=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con = dbmod.connect(self.db)
        try:
            con.execute("UPDATE reviews SET reviewed_at=?", (stale,))
            con.commit()
        finally:
            con.close()
        self.assertIn("error", undomod.undo(self.db))
        self.assertIn("older than 60 seconds",
                      undomod.section_html(self.db))

    def test_history_carries_undo(self):
        self.assertIn("id='undo'", histmod.history_html(self.db))


if __name__ == "__main__":
    unittest.main()
