"""Batch 14 integration: engines called from real paths, effects proven.

F-62 spacingopt drives sched.review_card via submit_review history;
F-61 interleave orders the Due queue via order_due. Per the
Integration rule, each test below proves a BEHAVIORAL effect (due
dates move, queue order changes) with the legacy path pinned as the
no-data fallback — not just demo rendering.
"""
import unittest

from groundwork import interleave as ilmod
from groundwork import sched as schedmod
from groundwork import spacingopt as spmod

from test_web import make_module


class SpacingIntegrationTest(unittest.TestCase):
    def test_legacy_default_untouched(self):
        base = schedmod.review_card(1.0, 0.5, 5)
        self.assertEqual(
            schedmod.review_card(1.0, 0.5, 5, grades=None), base)
        self.assertEqual(
            schedmod.review_card(1.0, 0.5, 5, grades=[]), base)
        self.assertEqual(
            schedmod.review_card(5.0, 0.5, 1, grades=[5, 5, 1]),
            schedmod.review_card(5.0, 0.5, 1))

    def test_streak_stretches_due(self):
        from datetime import timedelta
        now = schedmod.utcnow()
        plain = schedmod.review_card(4.0, 0.5, 5, now=now)
        fit = schedmod.review_card(4.0, 0.5, 5, now=now,
                                   grades=[5, 5, 5, 5])
        base = max(1, round(plain["stability"]))
        self.assertGreater(fit["due"], plain["due"])
        want = max(1, int(round(spmod.apply_streak(float(base), 4))))
        self.assertEqual(
            fit["due"],
            schedmod.iso(schedmod.parse_iso(plain["due"])
                         + timedelta(days=want - base)))

    def test_trailing_fail_means_base(self):
        # Streak only stretches; collapse is the stability model's job.
        hit = schedmod.review_card(9.0, 0.5, 2, grades=[5, 5, 5, 2])
        plain = schedmod.review_card(9.0, 0.5, 2)
        self.assertEqual(hit["due"], plain["due"])
        self.assertEqual(hit["stability"], plain["stability"])

    def test_forecast_default_untouched_streak_stretches(self):
        self.assertEqual(schedmod.forecast_gap(10), "≈10d")
        self.assertEqual(schedmod.forecast_gap("high"), "unknown")
        self.assertEqual(schedmod.forecast_gap(4, 2), "≈19d")
        self.assertEqual(schedmod.forecast_gap(4, 0), "≈4d")
        self.assertEqual(schedmod.forecast_gap(4, "junk"), "≈4d")

    def test_submit_review_stretches_with_history(self):
        # Seed history with direct inserts (submitting would consume
        # the queue and run stability away); one live submit must then
        # stretch past the legacy recomputation from the same state.
        import sqlite3
        tmp, db, server, out = make_module("spacing live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        con = sqlite3.connect(db)
        try:
            con.executemany(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?,?,?)", [(card["id"], 5, 4)] * 3)
            con.commit()
            row = con.execute(
                "SELECT stability, difficulty FROM cards WHERE id=?",
                (card["id"],)).fetchone()
        finally:
            con.close()
        legacy = schedmod.review_card(row[0], row[1], 5)
        out = server.submit_review(card["id"], "5", 4)
        self.assertNotIn("error", out)
        # Three trailing 5s + this one: streak 4 stretches past legacy.
        self.assertGreater(out["next_due"], legacy["due"])


class InterleaveIntegrationTest(unittest.TestCase):
    def _cards(self):
        return [
            {"id": 1, "concept_id": "cA", "exercise_type": 1},
            {"id": 2, "concept_id": "cA", "exercise_type": 1},
            {"id": 3, "concept_id": "cB", "exercise_type": 1},
        ]

    def test_empty_mastery_falls_back_identical(self):
        cards = self._cards()
        for blank in (None, {}, "junk", []):
            self.assertEqual(
                [c["id"] for c in ilmod.order_due(cards, blank)],
                [c["id"] for c in schedmod.interleave(cards)])
        self.assertEqual(ilmod.order_due([], {"cA": 1}), [])
        self.assertEqual(ilmod.order_due(None, {"cA": 1}), [])

    def test_weakest_cell_leads_with_contrast(self):
        cards = self._cards()
        mastery = {("cA", 1): 5.0, ("cB", 1): 1.0}
        ids = [c["id"] for c in ilmod.order_due(cards, mastery)]
        # Weakest cell first, then round-robin across ranked cells.
        self.assertEqual(ids, [3, 1, 2])

    def test_unknown_concepts_go_first_never_lost(self):
        cards = (self._cards() +
                 [{"id": 4, "concept_id": "cNew", "exercise_type": 1}])
        mastery = {("cA", 1): 5.0, ("cB", 1): 4.0}
        out = ilmod.order_due(cards, mastery)
        self.assertEqual(out[0]["id"], 4)  # unpracticed first
        self.assertEqual(sorted(c["id"] for c in out), [1, 2, 3, 4])
        # Plain-concept keys work too; garbage never raises/reorders badly.
        out2 = ilmod.order_due(cards, {"cA": 5.0, "cB": 1.0})
        self.assertEqual(sorted(c["id"] for c in out2), [1, 2, 3, 4])
        out3 = ilmod.order_due(cards + ["junk", None],
                               {("cA", 1): "high"})
        self.assertEqual(sorted(c["id"] for c in out3), [1, 2, 3, 4])

    def test_due_listing_falls_back_live(self):
        tmp, db, server, out = make_module("interleave live")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(due)
        self.assertEqual(
            [c["id"] for c in due],
            [c["id"] for c in schedmod.interleave(list(due))])

    def test_due_listing_engages_with_mastery(self):
        # Seed mastery with direct inserts: submitting would reschedule
        # every card out of the queue (correctly) and leave nothing to
        # order. Weak concept must lead with no card lost or gained.
        import sqlite3
        tmp, db, server, out = make_module("interleave effect")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(due)
        weak_cid = due[0]["concept_id"]
        con = sqlite3.connect(db)
        try:
            weak = [c["id"] for c in due if c["concept_id"] == weak_cid]
            rest = [c["id"] for c in due if c["concept_id"] != weak_cid]
            con.executemany(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?,?,?)",
                [(i, 1, 2) for i in weak] + [(i, 5, 4) for i in rest])
            con.commit()
        finally:
            con.close()
        due2 = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertEqual(sorted(c["id"] for c in due2),
                         sorted(c["id"] for c in due))
        self.assertEqual(due2[0]["concept_id"], weak_cid)


if __name__ == "__main__":
    unittest.main()
