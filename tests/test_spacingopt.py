"""Spacing optimizer (F-62): gaps fitted to recall history."""
import unittest

from groundwork import spacingopt as spmod


class SpacingoptTest(unittest.TestCase):
    def test_passes_stretch_fails_collapse(self):
        self.assertEqual(spmod.next_interval([]), spmod.BASE_DAYS)
        self.assertEqual(spmod.next_interval([2]), spmod.BASE_DAYS)
        one = spmod.next_interval([5])
        two = spmod.next_interval([5, 5])
        self.assertGreater(one, spmod.BASE_DAYS)
        self.assertGreater(two, one)
        # A trailing fail wipes the streak, however long.
        self.assertEqual(spmod.next_interval([5, 5, 5, 1]),
                         spmod.BASE_DAYS)

    def test_growth_rate_and_ceiling(self):
        self.assertAlmostEqual(
            spmod.next_interval([4, 4], base=1.0), 1.0 * 2.2 ** 2)
        self.assertEqual(spmod.next_interval([5] * 30), spmod.MAX_DAYS)
        self.assertLessEqual(spmod.next_interval([5] * 30, base=9999),
                             spmod.MAX_DAYS)

    def test_pass_threshold_is_four(self):
        self.assertEqual(spmod.next_interval([3]), spmod.BASE_DAYS)
        self.assertGreater(spmod.next_interval([4]), spmod.BASE_DAYS)

    def test_garbage_never_raises_never_passes(self):
        for bad in (None, "junk", [None, "x", object()], float("nan")):
            self.assertEqual(spmod.next_interval(bad), spmod.BASE_DAYS)
        self.assertEqual(spmod.clean_grades([5, "x", None, 3]), [5, 3])
        self.assertEqual(spmod.next_interval([5], base="huge"),
                         spmod.BASE_DAYS * spmod.GROWTH)
        self.assertEqual(spmod.next_interval([5], base=-4),
                         spmod.BASE_DAYS * spmod.GROWTH)

    def test_describe_reads(self):
        self.assertIn("no recalls", spmod.describe([]))
        self.assertIn("straight passes", spmod.describe([5, 4, 5]))
        self.assertIn("fragile", spmod.describe([5, 5, 2]))
        self.assertIn("broken by", spmod.describe([2, 5, 5]))
        self.assertIsInstance(spmod.describe(None), str)

    def test_section_html_anchor(self):
        html = spmod.section_html()
        self.assertIn("id='status-b13-spacingopt'", html)
        self.assertIn("next_interval", html)

    def test_tour_entry_shape(self):
        e = spmod.tour_entry()
        self.assertEqual(e, {
            "id": "spacing-optimizer",
            "kind": "feature",
            "title": "Spacing optimizer",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-spacingopt",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "spacingopt.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
