"""Accepted disputes quarantine the card and regenerate it (I-195)."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import disputes as dismod
from groundwork import quarantine as quarmod

from test_web import make_module


def _row(db, sql, args=()):
    con = dbmod.connect(db)
    try:
        r = con.execute(sql, args).fetchone()
        return dict(r) if r is not None else None
    finally:
        con.close()


def _due_ids(server, limit=50):
    return [c["id"]
            for c in server.tool_list_due_reviews({"limit": limit})["due"]]


class QuarantineFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module(
            "quarantine mod")
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.cid = card["id"]

    def test_accepted_quarantines_and_regenerates_via_wire(self):
        # The resolve_dispute wire (not a direct call) settles accepted rows.
        filed = dismod.open_dispute(self.db, self.cid, "reference is wrong")
        out = dismod.resolve_dispute(
            self.db, filed["dispute_id"], "accepted")
        self.assertEqual(out["status"], "accepted")
        self.assertEqual(out["quarantined"], self.cid)
        self.assertTrue(quarmod.is_regen(out["regen_id"]))
        # Behavioral effect on the Due queue: bad card out, retry in.
        due = _due_ids(self.server)
        self.assertNotIn(self.cid, due)
        self.assertIn(out["regen_id"], due)
        old = _row(self.db, "SELECT stale FROM cards WHERE id=?",
                   (self.cid,))
        self.assertEqual(old["stale"], 1)
        new = _row(self.db, "SELECT * FROM cards WHERE id=?",
                   (out["regen_id"],))
        self.assertEqual(new["stale"], 0)
        self.assertEqual(new["lapses"], 0)
        self.assertEqual(new["stability"], 1.0)
        payload = json.loads(new["payload"])
        self.assertEqual(payload["regen_from"], self.cid)
        self.assertEqual(payload["regen_dispute"], filed["dispute_id"])
        self.assertEqual(payload["dispute_reason"], "reference is wrong")

    def test_settle_is_idempotent(self):
        filed = dismod.open_dispute(self.db, self.cid, "wrong ref")
        dismod.resolve_dispute(self.db, filed["dispute_id"], "accepted")
        second = quarmod.settle_accepted(self.db, filed["dispute_id"])
        self.assertTrue(second.get("reused"))
        n = _row(self.db, "SELECT COUNT(*) AS n FROM cards WHERE id LIKE ?",
                 (self.cid + quarmod.SEP + "%",))["n"]
        self.assertEqual(n, 1)

    def test_rejected_leaves_legacy_path_untouched(self):
        # Fallback pin: no quarantine, no regen, card stays due.
        filed = dismod.open_dispute(self.db, self.cid, "maybe wrong")
        out = dismod.resolve_dispute(
            self.db, filed["dispute_id"], "rejected")
        self.assertEqual(out["status"], "rejected")
        self.assertNotIn("quarantined", out)
        old = _row(self.db, "SELECT stale FROM cards WHERE id=?",
                   (self.cid,))
        self.assertEqual(old["stale"], 0)
        self.assertIn(self.cid, _due_ids(self.server))
        n = _row(self.db, "SELECT COUNT(*) AS n FROM cards WHERE id LIKE ?",
                 (self.cid + quarmod.SEP + "%",))["n"]
        self.assertEqual(n, 0)

    def test_open_dispute_is_noop(self):
        filed = dismod.open_dispute(self.db, self.cid, "still pending")
        out = quarmod.settle_accepted(self.db, filed["dispute_id"])
        self.assertEqual(out["status"], "open")
        self.assertFalse(out["quarantined"])

    def test_unknown_dispute_errors(self):
        self.assertIn("error", quarmod.settle_accepted(self.db, 9999))

    def test_pure_builders(self):
        self.assertEqual(quarmod.regen_id("m1:ex001", 7), "m1:ex001~rq7")
        self.assertTrue(quarmod.is_regen("m1:ex001~rq7"))
        self.assertFalse(quarmod.is_regen("m1:ex001"))
        self.assertFalse(quarmod.is_regen(None))
        new = quarmod.replacement_for(
            {"id": "m1:ex001", "concept_id": "m1:c", "exercise_type": "2",
             "front": "Q", "back": "A", "payload": "{}"},
            {"id": 7, "reason": "bad ref"}, "2026-01-01T00:00:00Z")
        self.assertEqual(new["id"], "m1:ex001~rq7")
        self.assertEqual(new["due"], "2026-01-01T00:00:00Z")
        self.assertEqual(new["front"], "Q")


if __name__ == "__main__":
    unittest.main()
