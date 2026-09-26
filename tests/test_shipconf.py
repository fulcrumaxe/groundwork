"""Ship-it confidence meter over diff coverage (F-133)."""
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import ownership as ownmod
from groundwork import shipconf as mod
from test_web import make_module


def _own(db):
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
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


def _empty_db():
    tmp = Path(tempfile.mkdtemp(prefix="gw-shipempty-"))
    db = str(tmp / "empty.db")
    dbmod.init_db(db)
    return db


class ShipconfUnitTest(unittest.TestCase):
    def test_confidence(self):
        self.assertEqual(mod.confidence(4, 5), 80)
        self.assertIsNone(mod.confidence(0, 0))
        self.assertEqual(mod.confidence(0, 5), 0)
        self.assertIsNone(mod.confidence(None, None))
        self.assertIsNone(mod.confidence(1, -2))

    def test_level(self):
        self.assertEqual(mod.level(None), "unknown")
        self.assertEqual(mod.level(85), "ship it")
        self.assertEqual(mod.level(60), "nearly there")
        self.assertEqual(mod.level(10), "risky")

    def test_window_counts_fresh_and_owned(self):
        _tmp, db, _server, _out = make_module("ship mod")
        fresh = mod.window_counts(db)
        self.assertGreaterEqual(fresh["modules"], 1)
        self.assertEqual((fresh["owned"], fresh["attempted"]), (0, 0))
        _own(db)
        owned = mod.window_counts(db)
        self.assertGreaterEqual(owned["owned"], 1)

    def test_window_counts_hostile(self):
        self.assertEqual(mod.window_counts("/nonexistent.db"),
                         {"owned": 0, "concepts": 0, "attempted": 0,
                          "modules": 0})


class ShipconfEffectTest(unittest.TestCase):
    def test_meter_empty_db_is_empty(self):
        self.assertEqual(mod.meter_html(_empty_db()), "")

    def test_meter_fresh_module_is_unknown(self):
        _tmp, db, _server, _out = make_module("ship fresh mod")
        out = mod.meter_html(db)
        self.assertIn("id='ship-confidence'", out)
        self.assertIn("unknown", out)
        self.assertNotIn("%", out)

    def test_meter_owned_shows_percent(self):
        _tmp, db, _server, _out = make_module("ship owned mod")
        _own(db)
        out = mod.meter_html(db)
        self.assertIn("% ship confidence", out)
        self.assertRegex(out, "ship it|nearly there|risky")

    def test_caller_history_gains_meter(self):
        _tmp, db, _server, _out = make_module("ship caller mod")
        _own(db)
        self.assertIn("ship-confidence", histmod.history_html(db))

    def test_caller_history_empty_is_legacy(self):
        self.assertNotIn("ship-confidence",
                         histmod.history_html(_empty_db()))


class ShipconfShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/reviews")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
