"""Flow detection (F-95): accuracy-plus-pace session extension."""
import unittest

from groundwork import flowdetect as mod
from groundwork import minisession as mmod


def att(grade, secs=20.0):
    return {"grade": grade, "secs": secs}


def card(cid):
    return {"id": cid, "due": f"2000-01-0{cid}T00:00:00Z"}


def rows(*pairs):
    """Newest-first review rows from (grade, reviewed_at) pairs."""
    return [{"grade": g, "reviewed_at": t} for g, t in pairs]


class AccuracyPaceTest(unittest.TestCase):
    def test_accuracy_share(self):
        rows_ = [att(5), att(4), att(5), att(2)]
        self.assertAlmostEqual(mod.accuracy(rows_), 0.75)

    def test_accuracy_empty_is_zero(self):
        self.assertEqual(mod.accuracy([]), 0.0)
        self.assertEqual(mod.accuracy(None), 0.0)

    def test_median_pace_odd_and_even(self):
        self.assertEqual(mod.median_pace([att(5, 10), att(5, 30), att(5, 20)]), 20.0)
        self.assertEqual(mod.median_pace([att(5, 10), att(5, 30)]), 20.0)

    def test_median_pace_missing_is_none(self):
        self.assertIsNone(mod.median_pace([{"grade": 5}]))
        self.assertIsNone(mod.median_pace([]))

    def test_clean_drops_bad_grades_keeps_window(self):
        cleaned = mod.clean_attempts(
            [{"grade": "x"}, att(5), {"grade": 9}, att(4), att(5), att(3),
             att(5), att(5), att(4)], window=5)
        self.assertEqual(len(cleaned), 5)
        self.assertTrue(all(0 <= r["grade"] <= 5 for r in cleaned))


class AttemptsWithPaceTest(unittest.TestCase):
    def test_deltas_become_secs_oldest_first(self):
        attempts = mod.attempts_with_pace(rows(
            (5, "2026-01-02T00:02:00Z"),
            (5, "2026-01-02T00:01:00Z"),
            (4, "2026-01-02T00:00:00Z")))
        self.assertEqual([a["grade"] for a in attempts], [4, 5, 5])
        self.assertEqual([a.get("secs") for a in attempts], [None, 60.0, 60.0])

    def test_session_break_has_no_pace_evidence(self):
        attempts = mod.attempts_with_pace(rows(
            (5, "2026-01-03T00:00:00Z"),
            (5, "2026-01-02T00:00:00Z")))
        self.assertEqual(len(attempts), 2)
        self.assertNotIn("secs", attempts[1])

    def test_hostile_never_raises(self):
        for bad in (None, [], "x", [{"nope": 1}],
                    [{"grade": 5, "reviewed_at": "junk"}]):
            out = mod.attempts_with_pace(bad)
            self.assertIsInstance(out, list)


class InFlowTest(unittest.TestCase):
    def test_flow_when_fast_and_accurate(self):
        self.assertTrue(mod.in_flow([att(5), att(4), att(5, 30), att(5)]))

    def test_no_flow_when_inaccurate(self):
        self.assertFalse(mod.in_flow([att(5), att(1), att(2, 10), att(5, 10)]))

    def test_no_flow_when_slow(self):
        self.assertFalse(mod.in_flow([att(5, 120), att(5, 100), att(4, 90)]))

    def test_no_flow_without_timing(self):
        self.assertFalse(mod.in_flow([{"grade": 5}] * 4))

    def test_legacy_no_data_fallback(self):
        for empty in ([], None, "garbage", [{"nope": 1}]):
            self.assertFalse(mod.in_flow(empty))

    def test_hostile_never_raises(self):
        for bad in (None, "x", 42, object(), [{"grade": None}]):
            self.assertFalse(mod.in_flow(bad))
            self.assertEqual(mod.bonus_count(bad), 0)
            self.assertEqual(mod.describe(bad), mod.describe([]))


class ExtendSessionTest(unittest.TestCase):
    """Behavioral-effect: Due minisession grows in flow, stands otherwise."""

    def test_extends_with_bonus_in_flow(self):
        picks = [card(1), card(2)]
        due = [card(1), card(2), card(3), card(4), card(5), card(6)]
        out = mod.extend_session(picks, due, [att(5), att(5), att(4), att(5)])
        self.assertGreater(len(out), len(picks))
        self.assertLessEqual(len(out), len(picks) + mod.MAX_BONUS)
        self.assertEqual(out[:2], picks)
        self.assertEqual(len({c["id"] for c in out}), len(out))

    def test_legacy_picks_stand_without_data(self):
        picks = [card(1), card(2)]
        due = [card(1), card(2), card(3)]
        for empty in ([], None):
            out = mod.extend_session(picks, due, empty)
            self.assertEqual(out, picks)
            self.assertIsNot(out, picks)

    def test_no_extension_out_of_flow(self):
        picks = [card(1)]
        due = [card(1), card(2), card(3)]
        out = mod.extend_session(picks, due, [att(1, 10)] * 4)
        self.assertEqual(out, picks)

    def test_never_mutates_inputs(self):
        picks = [card(1)]
        due = [card(1), card(2), card(3), card(4)]
        before = (list(picks), list(due))
        mod.extend_session(picks, due, [att(5)] * 5)
        self.assertEqual((picks, due), before)


class CallerEffectTest(unittest.TestCase):
    def _due(self, n=10):
        return [{"id": f"c{i:02d}", "concept": f"k{i % 3}",
                 "due": f"2026-09-20T{i:02d}:00:00Z"} for i in range(n)]

    def test_session_box_grows_in_flow(self):
        due = self._due(10)
        base = mmod.session_box_html(due, minutes=2,
                                     estimate_fn=lambda c: 60)
        flow_rows = rows((5, "2026-01-02T00:02:00Z"),
                         (5, "2026-01-02T00:01:00Z"),
                         (5, "2026-01-02T00:00:30Z"),
                         (4, "2026-01-02T00:00:00Z"))
        grown = mmod.session_box_html(
            due, minutes=2, estimate_fn=lambda c: 60,
            flow_attempts=mod.attempts_with_pace(flow_rows))
        import re
        base_n = int(re.search(r"About (\d+)", base).group(1))
        grown_n = int(re.search(r"About (\d+)", grown).group(1))
        self.assertGreater(grown_n, base_n)

    def test_session_box_stands_without_attempts(self):
        due = self._due(6)
        plain = mmod.session_box_html(due, minutes=5,
                                      estimate_fn=lambda c: 60)
        same = mmod.session_box_html(due, minutes=5,
                                     estimate_fn=lambda c: 60,
                                     flow_attempts=[])
        self.assertEqual(plain, same)

    def test_meta(self):
        self.assertIn("flow", mod.describe([att(5)] * 4))
        self.assertIn("too early", mod.describe([]))
        self.assertIn("id='status-b21-flowdetect'", mod.section_html())
        e = mod.tour_entry()
        self.assertEqual(e, {
            "id": "flow-detection",
            "kind": "feature",
            "title": "Flow detection",
            "blurb": "Nailing cards quickly? The session stretches a little — accuracy plus pace earns bonus cards.",
            "path": "/status",
            "anchor": "status-b21-flowdetect",
        })


if __name__ == "__main__":
    unittest.main()
