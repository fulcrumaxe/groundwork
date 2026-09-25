"""Regeneration status transparency (I-135)."""
import unittest

from groundwork import confusing as confmod
from groundwork import db as dbmod
from groundwork import regenstat as mod

from test_web import handler_for, make_module


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module(
            "regenstat mod")
        con = dbmod.connect(self.db)
        try:
            self.cid = con.execute(
                "SELECT id FROM concepts LIMIT 1").fetchone()[0]
            self.mid = con.execute(
                "SELECT module_id FROM concepts LIMIT 1").fetchone()[0]
        finally:
            con.close()
        self.key = f"{self.cid}#what-it-does"

    def test_empty_is_legacy_fallback(self):
        self.assertEqual(mod.flag_statuses(self.db, self.mid), [])
        self.assertEqual(mod.status_html(self.db, self.mid), "")

    def test_flagged_section_gets_position_and_age(self):
        confmod.record(self.db, self.key, "1")
        flags = mod.flag_statuses(self.db, self.mid)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["section"], self.key)
        self.assertEqual(flags[0]["position"], 1)
        body = mod.status_html(self.db, self.mid)
        self.assertIn("id='regen-status'", body)
        self.assertIn("awaiting rewrite", body)
        self.assertIn("#1 in queue", body)
        self.assertIn("(UTC)", body)

    def test_unflagged_leaves_status(self):
        confmod.record(self.db, self.key, "1")
        confmod.record(self.db, self.key, "0")
        self.assertEqual(mod.status_html(self.db, self.mid), "")

    def test_positions_order_oldest_first(self):
        key2 = f"{self.cid}#why-it-matters"
        confmod.record(self.db, self.key, "1")
        confmod.record(self.db, key2, "1")
        flags = mod.flag_statuses(self.db, self.mid)
        self.assertEqual([f["position"] for f in flags], [1, 2])
        self.assertEqual(flags[0]["section"], self.key)

    def test_hostile_empty(self):
        self.assertEqual(mod.flag_statuses(None, None), [])
        self.assertEqual(mod.status_html("/no/such.sqlite", "m"), "")
        self.assertEqual(mod.status_html(self.db, None), "")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "regen-status", "kind": "improvement",
            "title": "Regeneration status",
            "blurb": ("Every flagged section shows its queue position "
                      "and age — nothing waits silently."),
            "path": "/modules/{mid}", "anchor": "regen-status"})


class CallerEffectTest(unittest.TestCase):
    def test_module_page_shows_status_when_flagged(self):
        _tmp, db, _s, out = make_module("regenstat caller")
        mid = out["module_id"]
        con = dbmod.connect(db)
        try:
            cid = con.execute(
                "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
                (mid,)).fetchone()[0]
        finally:
            con.close()
        plain = handler_for(db).module_html(mid)
        self.assertNotIn("regen-status", plain)
        confmod.record(db, f"{cid}#what-it-does", "1")
        flagged = handler_for(db).module_html(mid)
        self.assertIn("id='regen-status'", flagged)
        self.assertIn("awaiting rewrite", flagged)


if __name__ == "__main__":
    unittest.main()
