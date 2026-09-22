"""Forgetting-curve personalization (F-91)."""
import unittest

from groundwork import forgetcurve as fcmod
from groundwork import sched as schedmod


def _rows(cid="c1", grades=(5, 5, 1), stability=10.0):
    return [{"card_id": cid, "stability": stability, "grade": g,
             "reviewed_at": f"2020-01-{10 + i:02d}T10:00:00Z"}
            for i, g in enumerate(grades)]


class CleanTest(unittest.TestCase):
    def test_events_skip_first_review(self):
        events = fcmod.clean_attempts(_rows())
        self.assertEqual(len(events), 2)
        stab, lag, ok = events[0]
        self.assertEqual((stab, lag, ok), (10.0, 1.0, True))

    def test_empty_and_hostile(self):
        self.assertEqual(fcmod.clean_attempts([]), [])
        self.assertEqual(fcmod.clean_attempts(None), [])
        self.assertEqual(fcmod.clean_attempts("nope"), [])


class FitTest(unittest.TestCase):
    def test_no_data_is_one(self):
        self.assertEqual(fcmod.fit_decay([]), 1.0)
        self.assertEqual(fcmod.fit_decay(None), 1.0)

    def test_fast_forgetter_above_one(self):
        events = fcmod.clean_attempts(_rows(grades=(5, 1, 1)))
        self.assertGreater(fcmod.fit_decay(events), 1.0)

    def test_slow_forgetter_below_one(self):
        events = fcmod.clean_attempts(_rows(grades=(1, 5, 5, 5)))
        self.assertLess(fcmod.fit_decay(events), 1.0)

    def test_clamped(self):
        self.assertLessEqual(fcmod.fit_decay([(0.01, 30.0, False)]),
                             fcmod.K_MAX)
        self.assertGreaterEqual(fcmod.fit_decay([(999.0, 0.0, True)]),
                                fcmod.K_MIN)


class CurveTest(unittest.TestCase):
    def test_none_k_is_legacy_exactly(self):
        for stab, lag in ((10.0, 3.0), (1.0, 0.0), (0.5, 30.0)):
            self.assertEqual(
                fcmod.personal_retrievability(stab, lag, None),
                schedmod.retrievability(stab, lag))

    def test_decay_moves_both_ways(self):
        base = fcmod.personal_retrievability(10.0, 9.0, 1.0)
        self.assertLess(fcmod.personal_retrievability(10.0, 9.0, 2.0), base)
        self.assertGreater(fcmod.personal_retrievability(10.0, 9.0, 0.5), base)

    def test_effective_stability(self):
        self.assertEqual(fcmod.effective_stability(10.0, 2.0), 5.0)
        self.assertEqual(fcmod.effective_stability(10.0, None), 10.0)


class OrderTest(unittest.TestCase):
    def _cards(self):
        return [{"id": "a", "stability": 10.0, "due": "2020-01-01T00:00:00Z"},
                {"id": "b", "stability": 1.0, "due": "2020-01-01T00:00:00Z"}]

    def test_fallback_keeps_order(self):
        cards = self._cards()
        self.assertEqual(fcmod.order_due(cards, None), cards)
        self.assertEqual(fcmod.order_due(cards, {}), cards)
        self.assertEqual([c["id"] for c in fcmod.order_due(cards, 1.0)],
                         ["a", "b"])
        self.assertEqual(fcmod.order_due(None, 2.0), [])

    def test_personalized_ranks_most_forgotten_first(self):
        out = fcmod.order_due(self._cards(), 2.0, now="2020-02-01")
        # Low stability + fast decay forgets hardest: b first.
        self.assertEqual([c["id"] for c in out], ["b", "a"])

    def test_slow_fader_same_weakest_first(self):
        out = fcmod.order_due(self._cards(), 0.5, now="2020-02-01")
        self.assertEqual([c["id"] for c in out], ["b", "a"])

    def test_per_card_decays_flip_input_order(self):
        cards = [{"id": "a", "stability": 5.0, "due": "2020-01-31T00:00:00Z"},
                 {"id": "b", "stability": 5.0, "due": "2020-01-01T00:00:00Z"}]
        out = fcmod.order_due(cards, {"a": 0.4}, now="2020-02-01")
        self.assertEqual([c["id"] for c in out], ["b", "a"])


class CallerEffectTest(unittest.TestCase):
    def test_due_keeps_order_without_history(self):
        from test_web import handler_for, make_module
        tmp, db, server, out = make_module("decay mod")
        h = handler_for(db)
        first = h.due_html()
        second = h.due_html()
        self.assertEqual(first, second)
        self.assertNotIn("forgetcurve", first)

    def test_dial_decay_param_is_backward_compatible(self):
        from groundwork import minisession as msmod
        cards = [{"id": "a", "stability": 10.0, "due": "2030-01-01T00:00:00Z",
                  "difficulty": 3}]
        self.assertEqual(msmod.apply_dial(cards, None), cards)
        kept = msmod.apply_dial(cards, "3", {}, decay=1.0)
        self.assertEqual([c["id"] for c in kept], ["a"])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{fcmod.STATUS_ANCHOR}'",
                      fcmod.section_html())
        e = fcmod.tour_entry()
        self.assertEqual(e["id"], "forgetting-curve")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], fcmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
