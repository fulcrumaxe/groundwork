"""A/B explainer phrasings kept by delayed recall (I-136)."""
import unittest

from groundwork import abphrase as mod
from groundwork import lessons as lesmod

from test_web import handler_for, make_module


def _lesson():
    return {"name": "add", "kind": "function", "summary": "Adds two numbers.",
            "docstring": "Return a + b.", "how": ["Take a.", "Add b."],
            "file": "calc.py", "line": 1, "callers": [], "callees": [],
            "eli5": {"analogy": "Like a piggy bank that only takes twos.",
                     "takeaway": "Defaults do the adding."},
            "tradeoffs": ["Inline the sum"]}


class VariantTest(unittest.TestCase):
    def test_deterministic_and_covering(self):
        seen = {mod.variant_for(f"cid-{i}") for i in range(50)}
        self.assertEqual(seen, {"A", "B"})
        self.assertEqual(mod.variant_for("x"), mod.variant_for("x"))

    def test_hostile_is_a(self):
        for bad in (None, "", [], {}, 0):
            self.assertEqual(mod.variant_for(bad), "A")

    @staticmethod
    def _ab_pair():
        seen = {}
        for i in range(50):
            cid = f"pair-{i}"
            seen.setdefault(mod.variant_for(cid), cid)
            if "A" in seen and "B" in seen:
                return seen["A"], seen["B"]
        raise AssertionError("no A/B pair in 50 candidates")

    def test_scoring_picks_recall_winner(self):
        cid_a, cid_b = self._ab_pair()
        win_cid, lose_cid = (cid_b, cid_a)
        rows = [(lose_cid, 5, "2026-01-01T10:00:00Z"),
                (lose_cid, 2, "2026-01-08T10:00:00Z"),
                (win_cid, 5, "2026-01-01T10:00:00Z"),
                (win_cid, 5, "2026-01-08T10:00:00Z")]
        out = mod.score_variants(rows)
        self.assertEqual(out["winner"], "B")
        self.assertEqual(out["total"], 2)

    def test_first_review_studies_not_recalls(self):
        out = mod.score_variants([("c", 5, "2026-01-01T10:00:00Z")])
        self.assertEqual(out["total"], 0)
        self.assertEqual(out["winner"], "")

    def test_tie_or_empty_no_winner(self):
        self.assertEqual(mod.score_variants([])["winner"], "")
        rows = [("a", 5, "2026-01-01T10:00:00Z"),
                ("a", 5, "2026-01-08T10:00:00Z"),
                ("b", 5, "2026-01-01T10:00:00Z"),
                ("b", 5, "2026-01-08T10:00:00Z")]
        # Both recall at 100%: tie keeps no winner either way.
        out = mod.score_variants(rows)
        if out["A"]["n"] and out["B"]["n"]:
            self.assertEqual(out["winner"], "")

    def test_hostile_scores_empty(self):
        out = mod.score_variants(None)
        self.assertEqual(out["total"], 0)
        self.assertEqual(mod.variant_report(None)["total"], 0)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "ab-phrasings", "kind": "improvement",
            "title": "A/B explainer phrasings",
            "blurb": ("Half the lessons lead simple-first, half "
                      "tradeoffs-first — recall keeps the winner."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_b_swaps_extremes(self):
        lesson = _lesson()
        a = lesmod.render_levels(lesson, 0.0, 0, "auto", "/m",
                                 ab_variant="A")
        b = lesmod.render_levels(lesson, 0.0, 0, "auto", "/m",
                                 ab_variant="B")
        self.assertLess(a.index("piggy bank"), a.index("Adds two numbers"))
        self.assertLess(b.index("Adds two numbers"), b.index("piggy bank"))

    def test_legacy_default_is_a(self):
        lesson = _lesson()
        self.assertEqual(
            lesmod.render_levels(lesson, 0.0, 0, "auto", "/m"),
            lesmod.render_levels(lesson, 0.0, 0, "auto", "/m",
                                 ab_variant="A"))

    def test_module_page_assigns_deterministically(self):
        _tmp, db, _s, out = make_module("abphrase caller")
        first = handler_for(db).module_html(out["module_id"])
        second = handler_for(db).module_html(out["module_id"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
