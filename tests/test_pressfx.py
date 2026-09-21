"""Sound-free haptic-style press micro-interactions (I-80)."""
import re
import unittest

from groundwork import pressfx as pxmod


class PressFxTest(unittest.TestCase):
    def test_active_scale_targets_real_button_and_card_selectors(self):
        css = pxmod.pressfx_css()
        for sel in ("button", ".btn", "input[type=submit]", ".card-link"):
            self.assertIn(sel, css)
        self.assertIn(":active", css)
        self.assertIn("scale(0.97)", css.replace(" ", ""))
        self.assertIn("transform", css)

    def test_duration_well_under_150ms_cap(self):
        css = pxmod.pressfx_css()
        durations = [int(m.group(1))
                     for m in re.finditer(r"(\d+)\s*ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLessEqual(ms, 150)

    def test_reduced_motion_override_disables_press(self):
        css = pxmod.pressfx_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("transform:none", css)
        self.assertIn("transition:none", css)

    def test_focus_visible_outlines_untouched(self):
        css = pxmod.pressfx_css().lower()
        self.assertNotIn("outline", css)
        self.assertNotIn(":focus", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = pxmod.pressfx_css().lower()
        self.assertNotIn("<style", css)
        self.assertNotIn("</style", css)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "fast", True, -10, 9999, object()):
            ms = pxmod.duration_ms(bad)
            self.assertGreaterEqual(ms, 0)
            self.assertLessEqual(ms, 150)
        self.assertEqual(pxmod.selectors(),
                         ("button", ".btn", "input[type=submit]",
                          "input[type=button]", ".card-link"))

    def test_section_html_anchor(self):
        html = pxmod.section_html()
        self.assertIn("id='status-b12-pressfx'", html)

    def test_tour_entry_shape(self):
        e = pxmod.tour_entry()
        self.assertEqual(e["id"], "press-micro")
        self.assertEqual(e["kind"], "improvement")
        self.assertTrue(e["title"] and e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-pressfx")


if __name__ == "__main__":
    unittest.main()
