"""Fuller FSRS-4.5 parameters with per-learner fit (I-201).

Pure-model tests run standalone; the SchedulerIntegrationTest and the
submit test need the parent call site (review_card params/lag_days +
submit_review feeder) and prove the BEHAVIORAL effect: dues move with
fitted knobs, legacy stays pinned without them.
"""
import unittest
from datetime import timedelta

from groundwork import fsrs45 as fomod
from groundwork import sched as schedmod

from test_web import make_module

# Two cards x four reviews: passes at short lags, fails at long ones.
FAST_FADER = [
    ("A", 5, "2026-09-01T12:00:00Z"), ("A", 5, "2026-09-02T12:00:00Z"),
    ("A", 2, "2026-09-05T12:00:00Z"), ("A", 5, "2026-09-06T12:00:00Z"),
    ("B", 4, "2026-09-01T12:00:00Z"), ("B", 5, "2026-09-03T12:00:00Z"),
    ("B", 1, "2026-09-08T12:00:00Z"), ("B", 4, "2026-09-09T12:00:00Z"),
]
FIT = {"growth": 0.5, "decay": 1.6}


class RatingTest(unittest.TestCase):
    def test_grade_to_rating_map(self):
        self.assertEqual([fomod.to_rating(g) for g in range(6)],
                         [1, 1, 1, 2, 3, 4])

    def test_rating_garbage_is_again(self):
        for bad in (None, "x", object(), float("nan")):
            self.assertEqual(fomod.to_rating(bad), 1)


class AdvanceTest(unittest.TestCase):
    def test_first_review_initializes_from_tables(self):
        self.assertEqual(
            fomod.advance(1.0, 0.5, 5, params=dict(FIT), first=True)[0],
            5.0 * 0.5)  # S0(Easy) x growth
        self.assertAlmostEqual(
            fomod.advance(1.0, 0.5, 5, params=dict(FIT), first=True)[1],
            0.35)
        self.assertEqual(
            fomod.advance(9.0, 0.9, 1, params=None, first=True),
            (0.4, fomod.advance(9.0, 0.9, 1, first=True)[1]))
        self.assertAlmostEqual(
            fomod.advance(9.0, 0.9, 1, first=True)[1], 0.8)

    def test_gain_rises_as_retrievability_falls(self):
        kw = {"params": {"growth": 1.0, "decay": 1.0}}
        s1 = fomod.advance(4.0, 0.5, 4, lag_days=1.0, **kw)[0]
        s4 = fomod.advance(4.0, 0.5, 4, lag_days=4.0, **kw)[0]
        s20 = fomod.advance(4.0, 0.5, 4, lag_days=20.0, **kw)[0]
        self.assertGreater(s1, 4.0)
        self.assertGreater(s4, s1)
        self.assertGreater(s20, s4)
        self.assertAlmostEqual(s4, 5.147747, places=5)

    def test_hard_earns_less_than_good(self):
        kw = {"params": {"growth": 1.0, "decay": 1.0}, "lag_days": 4.0}
        hard = fomod.advance(4.0, 0.5, 3, **kw)[0]
        good = fomod.advance(4.0, 0.5, 4, **kw)[0]
        self.assertGreater(hard, 4.0)
        self.assertGreater(good, hard)

    def test_lapse_keeps_weighted_fraction(self):
        s, d = fomod.advance(4.0, 0.5, 1, lag_days=4.0,
                             params={"growth": 1.0, "decay": 1.0})
        self.assertAlmostEqual(s, 1.68)
        self.assertGreater(s, 0.1)
        self.assertLess(s, 4.0)

    def test_difficulty_drifts_then_reverts(self):
        up = fomod.advance(4.0, 0.5, 1, lag_days=4.0,
                           params={"growth": 1.0, "decay": 1.0})[1]
        down = fomod.advance(4.0, 0.5, 5, lag_days=4.0,
                             params={"growth": 1.0, "decay": 1.0})[1]
        self.assertGreater(up, 0.5)
        self.assertLess(down, 0.5)
        self.assertAlmostEqual(up, 0.636, places=3)

    def test_recall_prob_matches_sched_at_unit_decay(self):
        for s in (0.1, 1.0, 4.0, 16.0):
            for lag in (0, 1, 4, 20):
                self.assertEqual(fomod.recall_prob(s, lag),
                                 schedmod.retrievability(s, lag))
        self.assertLess(fomod.recall_prob(4.0, 4.0, 1.6),
                        fomod.recall_prob(4.0, 4.0, 1.0))
        self.assertGreater(fomod.recall_prob(4.0, 4.0, 0.6),
                           fomod.recall_prob(4.0, 4.0, 1.0))

    def test_days_since(self):
        from datetime import datetime, timezone
        fixed = datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(fomod.days_since("2026-09-06T12:00:00Z", fixed),
                         22.0)
        self.assertIsNone(fomod.days_since("junk"))
        self.assertIsNone(fomod.days_since(None))

    def test_garbage_never_raises(self):
        self.assertEqual(fomod.advance("x", None, object()), (1.0, 0.5))
        s, d = fomod.advance(float("inf"), float("nan"), -9)
        self.assertTrue(0.0 < s < 100.0 and 0.1 <= d <= 1.0)
        self.assertEqual(fomod.initial_stability("z"), 2.5)
        self.assertEqual(fomod.initial_difficulty(None), 0.5)
        self.assertEqual(fomod.recall_prob("x", "y"), 1.0)
        self.assertIsInstance(fomod.describe({"growth": "x"}), str)


class FitTest(unittest.TestCase):
    def test_fast_fader_fits_personal_knobs(self):
        self.assertEqual(fomod.fit(FAST_FADER), dict(FIT))
        got = fomod.fit(FAST_FADER)
        self.assertGreater(got["decay"], 1.0)
        self.assertLessEqual(got["growth"], 1.0)

    def test_thin_history_stays_legacy(self):
        self.assertIsNone(fomod.fit([]))
        self.assertIsNone(fomod.fit(None))
        self.assertIsNone(fomod.fit(FAST_FADER[:4]))  # 3 scored < 6
        self.assertIsNone(fomod.fit(["junk", None, (1,), {"nope": 1}]))

    def test_clean_sequences_shape(self):
        self.assertEqual(
            fomod.clean_sequences(FAST_FADER),
            [[(5, None), (5, 1), (2, 3), (5, 1)],
             [(4, None), (5, 2), (1, 5), (4, 1)]])

    def test_describe_reads(self):
        self.assertIn("no personal fit", fomod.describe(None))
        self.assertIn("fast fader", fomod.describe(dict(FIT)))
        self.assertIn("slow grower", fomod.describe(dict(FIT)))
        self.assertIn("slow fader",
                      fomod.describe({"growth": 1.4, "decay": 0.6}))

    def test_section_html_anchor(self):
        html = fomod.section_html()
        self.assertIn("id='status-b29-fsrs45'", html)
        self.assertIn("fsrs45.py", html)

    def test_tour_entry_shape(self):
        e = fomod.tour_entry()
        self.assertEqual(e, {
            "id": "fsrs45-fit",
            "kind": "improvement",
            "title": "Fuller FSRS fit",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b29-fsrs45",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "fsrs45.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


class SchedulerIntegrationTest(unittest.TestCase):
    def test_legacy_params_none_byte_identical(self):
        base = schedmod.review_card(4.0, 0.5, 5)
        self.assertEqual(
            schedmod.review_card(4.0, 0.5, 5, params=None, lag_days=99.0),
            base)
        self.assertEqual(
            schedmod.review_card(4.0, 0.5, 5, grades=[5, 5, 5, 5],
                                 params=None, lag_days=99.0),
            schedmod.review_card(4.0, 0.5, 5, grades=[5, 5, 5, 5]))

    def test_fitted_params_move_due(self):
        now = schedmod.utcnow()
        plain = schedmod.review_card(4.0, 0.5, 5, now=now)
        fitted = schedmod.review_card(4.0, 0.5, 5, now=now,
                                      params=dict(FIT), lag_days=4.0)
        self.assertNotEqual(fitted["due"], plain["due"])
        s, d = fomod.advance(4.0, 0.5, 5, lag_days=4.0, params=dict(FIT))
        self.assertAlmostEqual(fitted["stability"], s)
        self.assertAlmostEqual(fitted["difficulty"], d)
        self.assertEqual(
            fitted["due"],
            schedmod.iso(now + timedelta(days=max(1, round(s)))))

    def test_single_grade_history_initializes(self):
        now = schedmod.utcnow()
        out = schedmod.review_card(1.0, 0.5, 5, now=now, grades=[5],
                                   params=dict(FIT), lag_days=0.0)
        self.assertAlmostEqual(out["stability"], 2.5)  # S0(Easy) x 0.5
        self.assertAlmostEqual(out["difficulty"], 0.35)

    def test_fitted_path_composes_with_streak(self):
        now = schedmod.utcnow()
        bare = schedmod.review_card(4.0, 0.5, 5, now=now,
                                    params=dict(FIT), lag_days=4.0)
        stretched = schedmod.review_card(4.0, 0.5, 5, now=now,
                                         grades=[5, 5, 5, 5],
                                         params=dict(FIT), lag_days=4.0)
        self.assertGreaterEqual(stretched["due"], bare["due"])

    def test_submit_review_fits_global_history(self):
        import sqlite3
        tmp, db, server, out = make_module("fsrs45 live")
        cards = server.tool_list_due_reviews({"limit": 2})["due"]
        card_a = next(c for c in cards if int(c["exercise_type"]) == 1)
        card_b = next(c for c in cards if c["id"] != card_a["id"])
        seeds = [(card_a["id"], 5, "2026-09-01T12:00:00Z"),
                 (card_a["id"], 5, "2026-09-02T12:00:00Z"),
                 (card_a["id"], 2, "2026-09-05T12:00:00Z"),
                 (card_a["id"], 5, "2026-09-06T12:00:00Z"),
                 (card_b["id"], 4, "2026-09-01T12:00:00Z"),
                 (card_b["id"], 5, "2026-09-03T12:00:00Z"),
                 (card_b["id"], 1, "2026-09-08T12:00:00Z"),
                 (card_b["id"], 4, "2026-09-09T12:00:00Z")]
        con = sqlite3.connect(db)
        try:
            con.executemany(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
                " VALUES(?,?,?,?)",
                [(cid, g, 4, when) for cid, g, when in seeds])
            con.commit()
            row = con.execute(
                "SELECT stability, difficulty FROM cards WHERE id=?",
                (card_a["id"],)).fetchone()
        finally:
            con.close()
        legacy = schedmod.review_card(row[0], row[1], 5,
                                      grades=[5, 5, 2, 5, 5])
        out = server.submit_review(card_a["id"], "5", 4)
        self.assertNotIn("error", out)
        self.assertNotEqual(out["next_due"], legacy["due"])


if __name__ == "__main__":
    unittest.main()
