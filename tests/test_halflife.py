"""Team knowledge half-life report (F-182)."""
import unittest
from datetime import datetime, timedelta, timezone

from groundwork import halflife as hlmod
from groundwork import sched as schedmod


def _rows():
    # Two concepts: 'add' last seen 120 days ago (decayed), 'mul' fresh.
    return [
        {"concept": "add", "stability": 1.0,
         "reviewed_at": "2026-05-31T10:00:00Z"},
        {"concept": "add", "stability": 2.0,
         "reviewed_at": "2026-05-31T10:00:00Z"},
        {"concept": "mul", "stability": 10.0,
         "reviewed_at": "2026-09-20T10:00:00Z"},
    ]


NOW = "2026-09-28T00:00:00Z"


class HalfLifeTest(unittest.TestCase):
    def test_half_is_nine_stability(self):
        self.assertEqual(hlmod.half_life_days(1.0), 9.0)
        self.assertEqual(hlmod.half_life_days(10.0), 90.0)

    def test_hostile_is_zero(self):
        self.assertEqual(hlmod.half_life_days(None), 0.0)
        self.assertEqual(hlmod.half_life_days("nope"), 0.0)
        self.assertEqual(hlmod.half_life_days(-3.0), 0.0)

    def test_curve_hits_half_at_half_life(self):
        self.assertAlmostEqual(
            schedmod.retrievability(2.0, hlmod.half_life_days(2.0)), 0.5)


class RecallTest(unittest.TestCase):
    def test_elapsed_is_days_since_last_review(self):
        # Decision 281: t counts from the last review, not from due.
        self.assertEqual(hlmod.elapsed_days("2026-09-20T10:00:00Z", NOW), 8.0)
        self.assertIsNone(hlmod.elapsed_days("", NOW))
        self.assertIsNone(hlmod.elapsed_days(None, NOW))

    def test_current_recall_matches_sched_curve(self):
        self.assertEqual(
            hlmod.current_recall(10.0, "2026-09-20T10:00:00Z", NOW),
            schedmod.retrievability(10.0, 8.0))
        self.assertIsNone(hlmod.current_recall(10.0, "", NOW))

    def test_empty_and_hostile(self):
        self.assertEqual(hlmod.summarize([]), {})
        self.assertEqual(hlmod.summarize(None), {})
        self.assertEqual(hlmod.summarize("nope"), {})
        self.assertEqual(hlmod.decayed_since_quarter(None), [])


class SummarizeTest(unittest.TestCase):
    def test_per_concept_half_life_and_worst_recall(self):
        out = hlmod.summarize(_rows(), NOW)
        self.assertAlmostEqual(out["add"]["half_life"], 9.0 * 1.5)
        self.assertLess(out["add"]["recall"], 0.5)
        self.assertGreater(out["mul"]["recall"], 0.5)

    def test_decayed_flags_quarter_old_below_half(self):
        out = hlmod.summarize(_rows(), NOW)
        self.assertTrue(out["add"]["decayed"])
        self.assertFalse(out["mul"]["decayed"])

    def test_fresh_below_half_is_not_quarter_decay(self):
        rows = [{"concept": "new", "stability": 0.01,
                 "reviewed_at": "2026-09-27T10:00:00Z"}]
        out = hlmod.summarize(rows, NOW)
        self.assertLess(out["new"]["recall"], 0.5)
        self.assertFalse(out["new"]["decayed"])

    def test_worst_first(self):
        rows = _rows() + [{"concept": "zzz", "stability": 0.1,
                           "reviewed_at": "2026-01-01T10:00:00Z"}]
        got = hlmod.decayed_since_quarter(rows, NOW)
        self.assertEqual([e["concept"] for e in got], ["zzz", "add"])

    def test_undated_cards_keep_half_life_only(self):
        out = hlmod.summarize([{"concept": "ghost", "stability": 4.0,
                                "reviewed_at": ""}], NOW)
        self.assertEqual(out["ghost"]["half_life"], 36.0)
        self.assertIsNone(out["ghost"]["recall"])
        self.assertFalse(out["ghost"]["decayed"])


class SectionTest(unittest.TestCase):
    def _old_review_db(self, days_ago=120):
        from test_web import make_module
        tmp, db, server, out = make_module("half-life mod")
        import sqlite3
        stamp = (datetime.now(timezone.utc) - timedelta(days=days_ago)
                 ).strftime("%Y-%m-%dT%H:%M:%SZ")
        con = sqlite3.connect(db)
        try:
            cid = con.execute("SELECT id FROM cards LIMIT 1").fetchone()[0]
            con.execute("INSERT INTO reviews (card_id, grade, confidence,"
                        " reviewed_at) VALUES (?, ?, ?, ?)",
                        (cid, 5, 5, stamp))
            con.commit()
        finally:
            con.close()
        return db

    def test_fallback_empty_without_quarterly_data(self):
        # LEGACY PIN: no quarter-old review renders exactly as before.
        from test_web import make_module
        _, db, _, _ = make_module("half-life fresh")
        self.assertEqual(hlmod.section_html(db), "")
        recent = self._old_review_db(days_ago=7)
        self.assertEqual(hlmod.section_html(recent), "")

    def test_effect_lists_decayed_concept(self):
        import sqlite3
        db = self._old_review_db(days_ago=120)
        con = sqlite3.connect(db)
        try:
            concept = con.execute(
                "SELECT name FROM concepts LIMIT 1").fetchone()[0]
        finally:
            con.close()
        html_out = hlmod.section_html(db)
        self.assertIn(f"id='{hlmod.HALFLIFE_ANCHOR}'", html_out)
        self.assertIn(concept, html_out)

    def test_quarter_old_but_holding_reports_clean(self):
        db = self._old_review_db(days_ago=120)
        import sqlite3
        con = sqlite3.connect(db)
        try:
            con.execute("UPDATE cards SET stability = 1000.0")
            con.commit()
        finally:
            con.close()
        html_out = hlmod.section_html(db)
        self.assertIn(f"id='{hlmod.HALFLIFE_ANCHOR}'", html_out)
        self.assertIn("Nothing decayed since last quarter", html_out)


class CallerEffectTest(unittest.TestCase):
    def test_history_byte_stable_without_quarterly_data(self):
        from test_web import handler_for, make_module
        _, db, _, _ = make_module("half-life caller fresh")
        h = handler_for(db)
        first = h.history_html()
        self.assertEqual(first, h.history_html())
        self.assertNotIn(f"id='{hlmod.HALFLIFE_ANCHOR}'", first)

    def test_history_gains_section_with_quarter_decay(self):
        from test_web import handler_for
        db = SectionTest()._old_review_db(days_ago=120)
        h = handler_for(db)
        self.assertIn(f"id='{hlmod.HALFLIFE_ANCHOR}'", h.history_html())

    def test_status_demo_always_renders(self):
        from test_web import make_module
        _, db, _, _ = make_module("half-life status")
        body = hlmod.status_html(db)
        self.assertIn(f"id='{hlmod.STATUS_ANCHOR}'", body)
        self.assertIn("decayed of", body)
        self.assertIn(f"id='{hlmod.STATUS_ANCHOR}'", hlmod.status_html(""))

    def test_tour_entry_shape(self):
        e = hlmod.tour_entry()
        self.assertEqual(e["id"], "knowledge-half-life")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], hlmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
