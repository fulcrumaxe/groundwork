"""Explainer level extremes (I-123)."""
import unittest

from groundwork import levelextremes as lxmod
from groundwork import lessons as lesmod


def _lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults."],
            "worked": None}


def _rich():
    return dict(_lesson(),
                eli5={"analogy": "A piggy bank for twos.",
                      "takeaway": "Defaults do the adding."},
                tradeoffs=["Inline the sum", "Keep a running total",
                           "Use reduce", "A fourth way"])


class Eli5Test(unittest.TestCase):
    def test_pair_and_empty(self):
        got = lxmod.eli5_for(_rich())
        self.assertEqual(got["takeaway"], "Defaults do the adding.")
        self.assertEqual(lxmod.eli5_for(_lesson()), {})
        self.assertEqual(lxmod.eli5_for(None), {})
        self.assertEqual(lxmod.eli5_html({}), "")


class TradeoffsTest(unittest.TestCase):
    def test_caps_three_and_needs_list(self):
        got = lxmod.tradeoffs_for(_rich())
        self.assertEqual(len(got["alternatives"]), 3)
        self.assertIn("avoid add", got["probe"])
        self.assertEqual(lxmod.tradeoffs_for(_lesson()), {})
        self.assertEqual(lxmod.tradeoffs_html({}), "")


class HtmlTest(unittest.TestCase):
    def test_escapes(self):
        out = lxmod.eli5_html({"analogy": "<b>x", "takeaway": "y"})
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)


class LegacyTest(unittest.TestCase):
    def test_no_data_means_empty_pair(self):
        self.assertEqual(lxmod.extreme_blocks(_lesson()), ("", ""))
        self.assertEqual(lxmod.extreme_blocks(None), ("", ""))


class CallerEffectTest(unittest.TestCase):
    def test_render_levels_legacy_byte_identical(self):
        base = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertNotIn("extremes-", base)

    def test_extremes_wrap_active_level(self):
        out = lesmod.render_levels(_rich(), 0.0, 0, "auto", "/")
        self.assertIn("extremes-eli5", out)
        self.assertIn("extremes-tradeoffs", out)
        self.assertLess(out.index("extremes-eli5"), out.index("Explain it"))
        self.assertGreater(out.index("extremes-tradeoffs"),
                           out.index("Explain it back"))

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{lxmod.STATUS_ANCHOR}'",
                      lxmod.section_html())
        e = lxmod.tour_entry()
        self.assertEqual(e["id"], "level-extremes")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], lxmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
