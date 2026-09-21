"""Consistent custom carets for details/summary disclosures (I-60)."""
import unittest

from groundwork import carets as caretmod


class CaretsCssTest(unittest.TestCase):
    def test_targets_details_summary_selectors(self):
        css = caretmod.carets_css()
        for selector in ("summary{", "summary::before",
                         "summary::-webkit-details-marker",
                         "summary::marker",
                         "details[open]>summary::before"):
            self.assertIn(selector, css)

    def test_open_state_rotation_rule_present(self):
        css = caretmod.carets_css()
        _, _, open_rule = css.partition("details[open]>summary::before")
        self.assertIn("transform:rotate(", open_rule)
        closed, _, _ = css.partition("details[open]")
        self.assertIn("transform:rotate(", closed)
        self.assertNotEqual(
            closed.rsplit("transform:rotate(", 1)[-1].split(")", 1)[0],
            open_rule.split("transform:rotate(", 1)[-1].split(")", 1)[0])

    def test_native_marker_suppressed_cross_browser(self):
        css = caretmod.carets_css()
        self.assertIn("::-webkit-details-marker", css)
        self.assertIn("display:none", css)
        self.assertIn("summary::marker", css)

    def test_no_style_tags_no_network(self):
        css = caretmod.carets_css().lower()
        self.assertNotIn("<style", css)
        for marker in ("http", "url(", "@import", "@font-face"):
            self.assertNotIn(marker, css)

    def test_no_disclosure_breakage_markers(self):
        # Markers that would hide or break details/summary rendering
        # must never appear: display:none / visibility:hidden applied
        # outside the marker-suppression rule, or list-style resets
        # that reintroduce native triangles.
        css = caretmod.carets_css().lower()
        self.assertNotIn("visibility:hidden", css)
        self.assertNotIn("summary{display:none", css.replace(" ", ""))
        self.assertNotIn("details{display:none", css.replace(" ", ""))
        self.assertNotIn("<li", css)
        self.assertIn("list-style:none", css.replace(" ", ""))

    def test_css_drawn_not_glyph_swapped(self):
        css = caretmod.carets_css()
        self.assertIn("summary::before", css)
        self.assertIn("border-right", css)
        self.assertIn("border-bottom", css)
        self.assertIn("currentColor", css)

    def test_has_caret_rules_accepts_wired_css(self):
        self.assertTrue(caretmod.has_caret_rules(caretmod.carets_css()))

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "", 5, ["summary"], object()):
            self.assertFalse(caretmod.has_caret_rules(bad))
        self.assertFalse(caretmod.has_caret_rules("summary{color:red}"))

    def test_section_html_anchor(self):
        html = caretmod.section_html()
        self.assertIn("id='status-b10-carets'", html)


if __name__ == "__main__":
    unittest.main()
