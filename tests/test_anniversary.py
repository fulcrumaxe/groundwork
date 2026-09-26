"""Anniversary recaps: your year in code comprehension (F-132)."""
import unittest
from datetime import timedelta

from groundwork import anniversary as mod
from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import sched as schedmod
from test_web import make_module


def _row(when, grade=5, module="m"):
    return {"reviewed_at": when, "grade": grade, "module": module}


class AnniversaryUnitTest(unittest.TestCase):
    def test_empty_is_ineligible(self):
        r = mod.summarize([], 0, "2026-09-26")
        self.assertFalse(r["eligible"])
        self.assertEqual(mod.recap_html(r), "")

    def test_single_day_is_ineligible(self):
        r = mod.summarize([_row("2026-09-26T10:00:00Z")], 0, "2026-09-26")
        self.assertFalse(r["eligible"])

    def test_year_span_is_eligible(self):
        rows = [_row("2025-08-01T10:00:00Z", 2, "old"),
                _row("2026-09-01T10:00:00Z", 5, "new"),
                _row("2026-09-26T10:00:00Z", 5, "new")]
        r = mod.summarize(rows, 3, "2026-09-26")
        self.assertTrue(r["eligible"])
        self.assertEqual(r["attempts"], 2)  # pre-window row excluded
        self.assertEqual(r["owned"], 3)
        self.assertEqual(r["acc"], 100)
        self.assertEqual(r["top"][0]["module"], "new")

    def test_trend_halves(self):
        rows = [_row("2025-08-01T10:00:00Z", 2, "m"),
                _row("2026-01-01T10:00:00Z", 2, "m"),
                _row("2026-09-01T10:00:00Z", 5, "m"),
                _row("2026-09-02T10:00:00Z", 5, "m")]
        r = mod.summarize(rows, 0, "2026-09-26")
        t0, t1 = r["trend"]
        self.assertEqual(t0, "0%")
        self.assertEqual(t1, "100%")

    def test_top_capped_and_sorted(self):
        rows = ([_row("2025-08-01T10:00:00Z", 5, "zz")] +
                [_row(f"2026-09-{d:02d}T10:00:00Z", 5, m)
                 for d, m in [(1, "b"), (2, "a"), (3, "b"), (4, "c"),
                              (5, "d"), (6, "a")]])
        r = mod.summarize(rows, 0, "2026-09-26")
        self.assertEqual([t["module"] for t in r["top"]], ["a", "b", "c"])

    def test_hostile_fails_closed(self):
        r = mod.summarize([None, 42, {"x": 1}, ("bad",)], "many", None)
        self.assertFalse(r["eligible"])
        self.assertEqual(mod.recap_html(None), "")
        self.assertEqual(mod.recap_html({}), "")
        self.assertFalse(mod.eligible("junk", "junk"))

    def test_recap_escapes_and_names_year(self):
        r = mod.summarize([_row("2025-08-01T10:00:00Z", 5, "<b>"),
                           _row("2026-09-01T10:00:00Z", 5, "<b>")],
                          1, "2026-09-26")
        out = mod.recap_html(r)
        self.assertIn("year in code comprehension", out)
        self.assertNotIn("<b>", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("streak", out.casefold())


class AnniversaryEffectTest(unittest.TestCase):
    def _aged_db(self):
        _tmp, db, _server, _out = make_module("anniversary mod")
        from groundwork import db as dbmod
        now = schedmod.utcnow()
        old = (now - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        new = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        con = dbmod.connect(db)
        try:
            card = con.execute("SELECT id FROM cards LIMIT 1").fetchone()[0]
            for when in (old, new):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at) VALUES(?, 5, 4, ?)", (card, when))
            con.commit()
        finally:
            con.close()
        return db

    def test_caller_history_gains_recap_with_year(self):
        db = self._aged_db()
        body = histmod.history_html(db)
        self.assertIn("id='anniversary'", body)
        self.assertIn("Your year", body)

    def test_fresh_module_keeps_legacy_bytes(self):
        _tmp, db, _server, _out = make_module("anniversary fresh mod")
        self.assertEqual(mod.block_html(db), "")
        self.assertNotIn("id='anniversary'", histmod.history_html(db))


class AnniversaryShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
