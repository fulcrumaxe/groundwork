"""Time-invested ledger: hours in, owned out (F-105)."""
import unittest

from groundwork import db as dbmod
from groundwork import timeledger as mod

from test_web import handler_for, make_module


def _span_fixture():
    """Two practice days: 90 minutes on day one, 30 on day two."""
    tmp, db, server, out = make_module("timeledger mod")
    con = dbmod.connect(db)
    try:
        cid = con.execute(
            "SELECT id FROM cards LIMIT 1").fetchone()[0]
        con.execute("DELETE FROM reviews")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 4, 3, '2026-01-01T10:00:00Z')", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 4, 3, '2026-01-01T11:30:00Z')", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 4, 3, '2026-01-03T09:00:00Z')", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 4, 3, '2026-01-03T09:30:00Z')", (cid,))
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class LedgerTest(unittest.TestCase):
    def test_daily_spans_capped(self):
        _tmp, db, _s, _o = _span_fixture()
        spans = mod.daily_spans(db)
        self.assertEqual([d for d, _ in spans],
                         ["2026-01-01", "2026-01-03"])
        self.assertAlmostEqual(spans[0][1], 90.0)
        self.assertAlmostEqual(spans[1][1], 30.0)

    def test_ledger_totals(self):
        _tmp, db, _s, _o = _span_fixture()
        L = mod.ledger(db)
        self.assertAlmostEqual(L["minutes"], 120.0)
        self.assertEqual(L["days"], 2)
        self.assertEqual(L["owned"], 0)

    def test_day_cap(self):
        self.assertLessEqual(mod.DAY_CAP_MINUTES, 360.0)
        spans = mod.daily_spans(None)
        self.assertEqual(spans, [])

    def test_hostile_zeros(self):
        self.assertEqual(mod.ledger(None),
                         {"minutes": 0.0, "days": 0, "owned": 0})
        self.assertEqual(mod.ledger("/no/such/db.sqlite"),
                         {"minutes": 0.0, "days": 0, "owned": 0})

    def test_format(self):
        self.assertEqual(mod._fmt_minutes(90), "1h 30m")
        self.assertEqual(mod._fmt_minutes(5), "5m")
        self.assertEqual(mod._fmt_minutes(None), "0m")


class SectionTest(unittest.TestCase):
    def test_section_always_anchored(self):
        _tmp, db, _s, _o = make_module("timeledger anchor")
        self.assertIn("id='time-ledger'", mod.section_html(db))

    def test_section_names_investment(self):
        _tmp, db, _s, _o = _span_fixture()
        body = mod.section_html(db)
        self.assertIn("2h 0m", body)
        self.assertIn("2 days", body)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "time-ledger", "kind": "feature",
            "title": "Time ledger",
            "blurb": ("Your invested hours against concepts owned — the "
                      "honest ROI of practice."),
            "path": "/reviews", "anchor": "time-ledger"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_ledger(self):
        _tmp, db, server, _o = make_module("timeledger caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='time-ledger'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("timeledger empty")
        body = handler_for(db).history_html()
        self.assertIn("id='time-ledger'", body)


if __name__ == "__main__":
    unittest.main()
