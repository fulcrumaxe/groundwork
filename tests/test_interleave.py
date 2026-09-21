"""Interleaving engine v2 (F-61): weakest cell, never same twice."""
import unittest

from groundwork import interleave as ilmod


class InterleaveTest(unittest.TestCase):
    def test_weakest_first_with_contrast(self):
        cells = [("retry", "predict", 0.2), ("retry", "author", 0.8),
                 ("cache", "predict", 0.4), ("cache", "author", 0.6)]
        picks = ilmod.schedule(cells, 4)
        self.assertEqual(picks[0], ("retry", "predict", 0.2))
        self.assertTrue(ilmod.is_interleaved(picks))
        self.assertEqual(len(picks), 4)

    def test_no_same_concept_runs_when_avoidable(self):
        cells = [(f"c{i % 3}", f"t{i}", (i % 5) / 5.0) for i in range(12)]
        picks = ilmod.schedule(cells, 9)
        self.assertTrue(ilmod.is_interleaved(picks))

    def test_single_concept_degrades_honestly(self):
        cells = [("only", "a", 0.9), ("only", "b", 0.1)]
        picks = ilmod.schedule(cells, 2)
        self.assertEqual(picks[0][1], "b")  # weakest still first
        self.assertTrue(ilmod.is_interleaved(picks))  # vacuous, 1 concept

    def test_mastery_clamped_bad_cells_skipped(self):
        cells = [("a", "x", 9.0), ("b", "y", -2.0), ("c", "z", "nan"),
                 ("", "z", 0.1), ("d", "", 0.1), "junk", None]
        clean = ilmod.clean_cells(cells)
        self.assertEqual([(c[0], c[1]) for c in clean],
                         [("a", "x"), ("b", "y"), ("c", "z")])
        self.assertEqual(clean[0][2], 1.0)
        self.assertEqual(clean[1][2], 0.0)
        self.assertEqual(clean[2][2], 0.0)

    def test_count_clamped_never_raises(self):
        cells = [("a", "x", 0.1), ("b", "y", 0.2)]
        self.assertEqual(len(ilmod.schedule(cells, 0)), 1)
        self.assertLessEqual(len(ilmod.schedule(cells, 999)), 2)
        self.assertEqual(ilmod.schedule(cells, "many"), ilmod.schedule(cells, 6))
        self.assertEqual(ilmod.schedule(None, 4), [])
        self.assertEqual(ilmod.schedule("junk", 4), [])

    def test_is_interleaved_edge_cases(self):
        self.assertTrue(ilmod.is_interleaved([]))
        self.assertTrue(ilmod.is_interleaved([("a", "x", 0.1)]))
        self.assertFalse(ilmod.is_interleaved(
            [("a", "x", 0.1), ("a", "y", 0.2), ("b", "z", 0.3)]))
        self.assertTrue(ilmod.is_interleaved(None))  # empty: vacuous

    def test_section_html_anchor(self):
        html = ilmod.section_html()
        self.assertIn("id='status-b13-interleave'", html)
        self.assertIn("schedule", html)

    def test_tour_entry_shape(self):
        e = ilmod.tour_entry()
        self.assertEqual(e, {
            "id": "interleaving",
            "kind": "feature",
            "title": "Interleaving engine",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-interleave",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "interleave.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
