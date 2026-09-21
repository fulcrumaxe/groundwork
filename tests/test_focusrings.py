"""Focus-visible rings everywhere; outlines never removed (I-65)."""
import unittest

from groundwork import focusrings as frmod
from groundwork import palette as palettemod


class FocusringsTest(unittest.TestCase):
    def test_no_outline_removal_anywhere(self):
        css = frmod.css()
        for banned in ("outline:none", "outline: none",
                       "outline:0", "outline: 0"):
            self.assertNotIn(banned, css.replace("outline-offset", ""))

    def test_ring_tied_to_palette_token(self):
        self.assertIn(frmod.RING_COLOR_TOKEN, palettemod.PALETTE)
        self.assertIn(f"--focus-ring:var({frmod.RING_COLOR_TOKEN})",
                      frmod.css())

    def test_every_interactive_selector_covered(self):
        css = frmod.css()
        for sel in frmod.SELECTORS:
            self.assertIn(f"{sel}:focus-visible", css, sel)
        self.assertEqual(frmod.covered_selectors(css)["missing"], [])

    def test_audit_finds_gaps_and_fails_closed(self):
        rep = frmod.covered_selectors("a:focus-visible{outline:3px solid red}")
        self.assertIn("a", rep["covered"])
        self.assertIn("button", rep["missing"])
        for bad in (None, "", 123, ["a:focus-visible"]):
            rep = frmod.covered_selectors(bad)
            self.assertEqual(rep["covered"], [])
            self.assertEqual(rep["missing"], list(frmod.SELECTORS))

    def test_reduced_motion_keeps_static_ring(self):
        css = frmod.css()
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("transition:none", css)
        self.assertIn("outline:var(--focus-ring-width)", css)

    def test_css_is_raw_declarations_no_style_tags(self):
        self.assertNotIn("<style", frmod.css())

    def test_transition_clamped(self):
        self.assertEqual(frmod.transition_ms(9999), frmod.MAX_TRANSITION_MS)
        self.assertEqual(frmod.transition_ms(-5), 0)
        self.assertEqual(frmod.transition_ms("x"), frmod.TRANSITION_MS)

    def test_section_html_anchor(self):
        self.assertIn("id='status-b11-focusrings'", frmod.section_html())


if __name__ == "__main__":
    unittest.main()
