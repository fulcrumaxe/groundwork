"""Calibration-aware explainer levels (I-122)."""
import unittest

from groundwork import explain as explainmod
from groundwork import explcalib as ecmod
from groundwork import lessons as lesmod


def _lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults."],
            "worked": None}


OVER = [(2, 5)] * 6
UNDER = [(5, 1)] * 6


class RecentGapTest(unittest.TestCase):
    def test_none_empty_garbage_is_none(self):
        self.assertIsNone(ecmod.recent_gap(None))
        self.assertIsNone(ecmod.recent_gap([]))
        self.assertIsNone(ecmod.recent_gap(["nope", (None, None), ("a", "b")]))

    def test_overconfident_gap(self):
        self.assertAlmostEqual(ecmod.recent_gap(OVER), 0.6)

    def test_tail_uses_last_five(self):
        rows = [(5, 5)] * 10 + OVER
        self.assertAlmostEqual(ecmod.recent_gap(rows), 0.6)

    def test_rows_newest_first_by_default(self):
        rows = ecmod.recent_from_rows(
            [{"grade": 2, "confidence": 5}] * 6, newest_first=True)
        self.assertEqual(rows, [(2, 5)] * 6)
        self.assertAlmostEqual(ecmod.recent_gap(rows), 0.6)


class PickLevelTest(unittest.TestCase):
    def test_no_data_matches_auto_level_grid(self):
        for mastery in (0.0, 0.29, 0.3, 0.59, 0.6, 0.84, 0.85, 1.0):
            for n in (0, 1, 9):
                self.assertEqual(
                    ecmod.pick_level(mastery, n, None),
                    explainmod.auto_level(mastery, n))
                self.assertEqual(ecmod.pick_level(mastery, n, []),
                                 explainmod.auto_level(mastery, n))

    def test_hostile_falls_back(self):
        self.assertEqual(ecmod.pick_level("x", "y", "z"),
                         explainmod.auto_level(0.0, 0))

    def test_overconfident_steps_down(self):
        self.assertEqual(ecmod.pick_level(0.9, 9, OVER), 3)
        self.assertEqual(ecmod.pick_level(0.1, 9, OVER), 1)  # floor

    def test_shy_accurate_steps_up(self):
        self.assertEqual(ecmod.pick_level(0.5, 5, UNDER), 3)

    def test_low_accuracy_never_steps_up(self):
        rows = [(1, 1)] * 6  # failing and knows it
        self.assertEqual(ecmod.pick_level(0.5, 5, rows), 2)


class EffectTest(unittest.TestCase):
    def test_render_levels_legacy_without_recent(self):
        base = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/")
        self.assertIn("Expert", base)

    def test_render_levels_steps_down_on_overconfidence(self):
        out = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/",
                                   recent=OVER)
        self.assertIn("Intermediate", out)
        self.assertNotIn("Expert", out.split("Explain it")[0])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{ecmod.STATUS_ANCHOR}'",
                      ecmod.section_html())
        e = ecmod.tour_entry()
        self.assertEqual(e["id"], "calibration-levels")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], ecmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
