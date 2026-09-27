"""Handoff packs: export your owned map for a successor (F-160)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import handoff as mod
from groundwork import history as histmod
from groundwork import ownership as ownmod
from groundwork import share as sharemod

from test_web import make_module


def _earn_owned(db):
    """One owned concept via two grade-5 modify/create reviews."""
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (ownmod.ownership_types()[0], card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


class PackTest(unittest.TestCase):
    def test_pack_is_valid_share_doc(self):
        tmp, db, server, out = make_module("handoff mod")
        pack = mod.build_pack(db, out["module_id"])
        self.assertEqual(pack["format"], "groundwork-module/1")
        self.assertIn("module", pack)
        self.assertIn("concepts", pack)
        self.assertIn("cards", pack)
        self.assertTrue(mod.is_pack(pack))
        self.assertEqual(pack["handoff"]["format"], "groundwork-handoff/1")
        self.assertFalse(mod.is_pack({}))
        self.assertFalse(mod.is_pack({"format": "groundwork-module/1"}))
        self.assertFalse(mod.is_pack(None))

    def test_pack_imports_through_existing_path(self):
        tmp, db, server, out = make_module("handoff export mod")
        _earn_owned(db)
        pack = mod.build_pack(db, out["module_id"])
        fresh = str(Path(tempfile.mkdtemp(prefix="gw-hand-")) / "fresh.db")
        res = sharemod.import_module(fresh, pack)
        self.assertEqual(res["status"], "imported")
        self.assertGreater(res["concepts"], 0)
        con = sqlite3.connect(fresh)
        try:
            n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(n, 0)  # privacy: no review rows cross
        dup = sharemod.import_module(fresh, pack)
        self.assertEqual(dup["status"], "skipped-duplicate")

    def test_unknown_module_raises(self):
        tmp, db, server, out = make_module("handoff unknown mod")
        with self.assertRaises(KeyError):
            mod.build_pack(db, "nope")

    def test_json_round_trips_disk(self):
        tmp, db, server, out = make_module("handoff json mod")
        pack = mod.build_pack(db, out["module_id"])
        text = mod.pack_json(pack)
        back = json.loads(text)
        self.assertTrue(mod.is_pack(back))
        self.assertEqual(back["handoff"]["owned_count"],
                         pack["handoff"]["owned_count"])


class CallerEffectTest(unittest.TestCase):
    def test_history_shows_live_owned_counts(self):
        """Behavioral effect: rendered History differs with live data."""
        tmp, db, server, out = make_module("handoff live mod")
        before = histmod.history_html(db)
        self.assertIn("id='handoff'", before)
        self.assertIn("Owned 0/1", before)
        _earn_owned(db)
        after = histmod.history_html(db)
        self.assertIn("id='handoff'", after)
        self.assertIn("Owned 1/1", after)
        self.assertIn("import-module", after)

    def test_fresh_db_placeholder_never_crashes(self):
        tmp, db, server, out = make_module("handoff fresh mod")
        self.assertEqual(mod.packs(db)[0]["owned"], 0)
        body = histmod.history_html(db)
        self.assertIn("id='handoff'", body)  # anchor-stable for the tour gate


class ShapeTest(unittest.TestCase):
    def test_status_anchor(self):
        tmp, db, server, out = make_module("handoff status mod")
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.status_html(db))

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("handoff-packs", "feature", "/reviews", "handoff"))


if __name__ == "__main__":
    unittest.main()
