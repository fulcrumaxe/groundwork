"""Seasonal events: Hacktober-style own-5 goal, streak-free (F-131)."""
import unittest
from datetime import date
from unittest import mock

from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import seasonevent as mod
from test_web import make_module


def _own_october(db):
    """Own the fixture concept with both passes dated in October."""
    from groundwork import db as dbmod
    from groundwork import ownership as ownmod
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
                " reviewed_at) VALUES(?, 5, 4, '2026-10-10T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


class FakeDate(date):
    @classmethod
    def today(cls):
        return date(2026, 10, 15)


class FakeJune(date):
    @classmethod
    def today(cls):
        return date(2026, 6, 15)


class SeasoneventUnitTest(unittest.TestCase):
    def test_window_bounds_inclusive(self):
        self.assertIsNotNone(mod.current_event("2026-10-01"))
        self.assertIsNotNone(mod.current_event("2026-10-31"))
        self.assertIsNone(mod.current_event("2026-09-30"))
        self.assertIsNone(mod.current_event("2026-11-01"))
        self.assertIsNone(mod.current_event("2026-05-05"))

    def test_date_object_and_garbage(self):
        self.assertIsNotNone(mod.current_event(date(2026, 10, 15)))
        self.assertIsNone(mod.current_event(date(2026, 9, 15)))
        self.assertEqual(mod.current_event("garbage"),
                         mod.current_event(None))

    def test_progress_counts_in_window_only(self):
        _tmp, db, _server, _out = make_module("season mod")
        _own_october(db)
        p = mod.progress(db, "2026-10-15")
        self.assertEqual((p["owned"], p["goal"], p["done"]), (1, 5, False))
        p = mod.progress(db, "2026-09-15")
        self.assertEqual((p["owned"], p["done"]), (0, False))

    def test_progress_hostile(self):
        p = mod.progress("/nonexistent.db", "2026-10-15")
        self.assertEqual((p["owned"], p["done"]), (0, False))


class SeasoneventEffectTest(unittest.TestCase):
    def test_section_active_in_october(self):
        _tmp, db, _server, _out = make_module("season active mod")
        _own_october(db)
        body = mod.section_html(db, "2026-10-15")
        self.assertIn("id='seasonal-event'", body)
        self.assertIn("1 of 5 owned", body)

    def test_section_omitted_outside_window(self):
        _tmp, db, _server, _out = make_module("season idle mod")
        _own_october(db)
        self.assertEqual(mod.section_html(db, "2026-09-15"), "")

    def test_caller_history_gains_section_in_october(self):
        _tmp, db, _server, _out = make_module("season caller mod")
        _own_october(db)
        with mock.patch.object(mod, "date", FakeDate):
            self.assertIn("id='seasonal-event'", histmod.history_html(db))

    def test_caller_history_legacy_outside_window(self):
        _tmp, db, _server, _out = make_module("season legacy mod")
        _own_october(db)
        with mock.patch.object(mod, "date", FakeJune):
            self.assertNotIn("seasonal-event", histmod.history_html(db))


class SeasoneventShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
