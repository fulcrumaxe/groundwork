"""Desired-retention setting with workload preview (I-202)."""
import unittest

from groundwork import db as dbmod
from groundwork import retention as retentionmod
from groundwork import workload as workloadmod

from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_clamps_numerics(self):
        self.assertEqual(retentionmod.normalize("0.99"), 0.95)
        self.assertEqual(retentionmod.normalize("0.5"), 0.7)
        self.assertEqual(retentionmod.normalize(0.8), 0.8)
        self.assertEqual(retentionmod.normalize(0.70), 0.7)

    def test_hostile_fails_closed_to_default(self):
        for bad in (None, "", "bogus", "NaN", "inf", "-inf",
                    True, False, [], {}, object()):
            self.assertEqual(retentionmod.normalize(bad), 0.9)

    def test_from_query(self):
        self.assertEqual(retentionmod.from_query(None), 0.9)
        self.assertEqual(retentionmod.from_query({}), 0.9)
        self.assertEqual(retentionmod.from_query({"retention": ["0.80"]}),
                         0.8)
        self.assertEqual(retentionmod.from_query({"retention": ["bogus"]}),
                         0.9)
        self.assertEqual(retentionmod.from_query({"retention": []}), 0.9)


class IntervalTest(unittest.TestCase):
    def test_default_reproduces_stored_rule(self):
        for s in (1.0, 2.0, 3.89):
            self.assertEqual(retentionmod.interval_for(s, 0.9), round(s))

    def test_stricter_means_sooner(self):
        self.assertLess(retentionmod.interval_for(2.0, 0.95),
                        retentionmod.interval_for(2.0, 0.70))

    def test_never_below_one_day(self):
        self.assertGreaterEqual(retentionmod.interval_for(0.1, 0.95), 1)


class PreviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module(
            "retention mod")
        self.h = handler_for(self.db)

    def _review_one(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        return card["id"]

    def test_default_matches_live_forecast_when_unreviewed(self):
        # No reviews yet: every projection IS the stored due date.
        live = workloadmod.buckets(self.db)
        proj = retentionmod.preview_buckets(self.db)
        self.assertEqual(len(proj), 30)
        self.assertEqual([n for _, n in proj], [n for _, n in live])

    def test_higher_retention_never_lightens_load(self):
        self._review_one()
        totals = [sum(n for _, n in retentionmod.preview_buckets(
            self.db, r, days=7)) for r in (0.70, 0.80, 0.90, 0.95)]
        self.assertEqual(totals, sorted(totals))

    def test_reviewed_card_moves_strictly(self):
        # Behavioral effect on live data: the reviewed card's own
        # stability/last-review project strictly sooner at 0.95.
        cid = self._review_one()
        con = dbmod.connect(self.db)
        try:
            row = con.execute(
                "SELECT stability, due FROM cards WHERE id=?",
                (cid,)).fetchone()
            lr = con.execute(
                "SELECT MAX(reviewed_at) AS lr FROM reviews WHERE card_id=?",
                (cid,)).fetchone()["lr"]
        finally:
            con.close()
        early = retentionmod.project_due(lr, row["due"], row["stability"],
                                         0.95)
        late = retentionmod.project_due(lr, row["due"], row["stability"],
                                        0.70)
        self.assertLess(early, late)

    def test_param_selects_preset(self):
        body = retentionmod.box_html(self.db, {"retention": ["0.70"]})
        self.assertIn("0.70</a> <b>(active)</b>", body)
        self.assertIn("At 0.70:", body)

    def test_legacy_no_param_path_is_default(self):
        # Fallback pin: absent/hostile param renders the 0.90 box.
        self.assertEqual(retentionmod.box_html(self.db),
                         retentionmod.box_html(self.db, None))
        body = retentionmod.box_html(self.db, {"retention": ["bogus"]})
        self.assertIn("0.90</a> <b>(active)</b>", body)
        self.assertIn("At 0.90:", body)

    def test_history_shows_retention_box(self):
        self._review_one()
        body = self.h.history_html()
        self.assertIn("id='retention'", body)
        self.assertIn("?retention=0.95", body)


if __name__ == "__main__":
    unittest.main()
