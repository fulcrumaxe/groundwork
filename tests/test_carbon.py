"""Carbon note: reviews graded on this device, zero cloud calls (F-149)."""
import sqlite3
import unittest

from groundwork import carbon as mod
from groundwork import history as histmod

from test_web import make_module


def _card_id(db):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT id FROM cards LIMIT 1").fetchone()[0]
    finally:
        con.close()


def _seed_reviews(db, n=3):
    cid = _card_id(db)
    con = sqlite3.connect(db)
    try:
        for i in range(n):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
                " VALUES(?, 5, 4, ?)",
                (cid, f"2026-09-{20 + i:02d}T10:00:00"))
        con.commit()
    finally:
        con.close()


class CountsTest(unittest.TestCase):
    def test_counts_matches_seeded_reviews(self):
        tmp, db, server, out = make_module("carbon mod")
        _seed_reviews(db, 3)
        c = mod.counts(db)
        self.assertEqual(c["reviews"], 3)
        self.assertGreaterEqual(c["days"], 1)

    def test_unreadable_db_reads_zero(self):
        self.assertEqual(mod.counts("/nonexistent/x.db"),
                         {"reviews": 0, "cards": 0, "days": 0})


class NoteForTest(unittest.TestCase):
    def test_formats_and_zero_cloud(self):
        note = mod.note_for({"reviews": 1234})
        self.assertIn("1,234 reviews", note["line"])
        self.assertIn("0 cloud GPU calls", note["line"])
        self.assertEqual(note["cloud_calls"], 0)

    def test_zero_state(self):
        for bad in ({}, {"reviews": 0}, None, {"reviews": -2},
                    {"reviews": "lots"}, "x"):
            note = mod.note_for(bad)
            self.assertIn("No reviews yet", note["line"])
            self.assertEqual(note["cloud_calls"], 0)


class CallerEffectTest(unittest.TestCase):
    def test_history_shows_live_carbon_note(self):
        """Behavioral effect: History differs on live review data."""
        tmp, db, server, out = make_module("carbon live mod")
        _seed_reviews(db, 3)
        body = histmod.history_html(db)
        self.assertIn("id='carbon'", body)
        self.assertIn("3 reviews graded on this device", body)
        self.assertIn("0 cloud GPU calls", body)

    def test_fresh_history_shows_zero_state(self):
        tmp, db, server, out = make_module("carbon fresh mod")
        body = histmod.history_html(db)
        self.assertIn("id='carbon'", body)
        self.assertIn("No reviews yet", body)
        # Empty branch unbroken: art + Due link still render.
        self.assertIn("/due", body)

    def test_legacy_fallback(self):
        self.assertEqual(mod.section_html("/nonexistent/x.db"), "")


class ShapeTest(unittest.TestCase):
    def test_status_anchor(self):
        tmp, db, server, out = make_module("carbon status mod")
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.status_html(db))

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("carbon-note", "feature", "/reviews", "carbon"))


if __name__ == "__main__":
    unittest.main()
