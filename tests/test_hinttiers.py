"""Hint tiers: nudge, pointer, worked step (I-63)."""
import unittest

from groundwork import hinttiers as hintmod


class HintTiersTest(unittest.TestCase):
    def test_tier_order(self):
        self.assertEqual(hintmod.tier_of(0), "nudge")
        self.assertEqual(hintmod.tier_of(1), "pointer")
        self.assertEqual(hintmod.tier_of(2), "worked")

    def test_long_lists_keep_first_nudge_last_worked(self):
        self.assertEqual(hintmod.tier_of(0, 5), "nudge")
        self.assertEqual(hintmod.tier_of(4, 5), "worked")
        self.assertEqual(hintmod.tier_of(2, 5), "pointer")
        self.assertEqual(hintmod.tier_of(99, 5), "worked")
        self.assertEqual(hintmod.tier_of(-3, 5), "nudge")

    def test_unknown_fails_closed(self):
        self.assertEqual(hintmod.tier_class("bogus"), "hint-nudge")
        self.assertEqual(hintmod.tier_class(None), "hint-nudge")
        self.assertEqual(hintmod.tier_of("x"), "nudge")
        self.assertEqual(hintmod.tier_label(["nudge"]), "Nudge")
        self.assertEqual(hintmod.hint_html(""), "")
        self.assertEqual(hintmod.hint_html(None), "")
        self.assertEqual(hintmod.hints_html(None), "")
        self.assertEqual(hintmod.hints_html("nope"), "")

    def test_mapping_covers_all_tiers(self):
        classes = {hintmod.tier_class(t) for t in hintmod.TIERS}
        labels = {hintmod.tier_label(t) for t in hintmod.TIERS}
        self.assertEqual(len(classes), 3)
        self.assertEqual(len(labels), 3)
        for label in labels:
            self.assertTrue(label)

    def test_progressive_prefix_preserved(self):
        hints = ["a", "b", "c"]
        one = hintmod.hints_html(hints, attempts=0)
        self.assertIn("a", one)
        self.assertNotIn(">b<", one)
        two = hintmod.hints_html(hints, attempts=1)
        self.assertIn("b", two)
        self.assertNotIn(">c<", two)
        self.assertIn("c", hintmod.hints_html(hints, attempts=99))
        self.assertEqual(hintmod.hints_html([], attempts=0), "")

    def test_html_escapes_hint_text(self):
        out = hintmod.hint_html("<script>alert(1)</script>", 0)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("details", out)
        self.assertIn("hint-nudge", out)
        self.assertIn("hint-tag", out)
        self.assertIn("id='hints'", hintmod.hints_html(["x"]))

    def test_css_no_style_tags_no_network(self):
        css = hintmod.hinttiers_css().lower()
        for banned in ("<style", "http", "url(", "@import", "@font-face"):
            self.assertNotIn(banned, css)
        for sel in (".hint-nudge", ".hint-pointer", ".hint-worked"):
            self.assertIn(sel, css)
        self.assertIn("details[open]", hintmod.hinttiers_css())
        self.assertIn("prefers-reduced-motion", hintmod.hinttiers_css())

    def test_audit_accepts_wired_css(self):
        self.assertTrue(hintmod.has_hinttier_rules(hintmod.hinttiers_css()))
        self.assertFalse(hintmod.has_hinttier_rules(""))
        self.assertFalse(hintmod.has_hinttier_rules(".hint-nudge{}"))
        self.assertFalse(hintmod.has_hinttier_rules(None))

    def test_no_disclosure_breakage(self):
        css = hintmod.hinttiers_css().replace("outline-offset", "")
        for banned in ("display:none", "display: none"):
            self.assertNotIn(banned, css)


if __name__ == "__main__":
    unittest.main()
