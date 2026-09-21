"""Animate progress bars with width transitions (I-57)."""
import re
import unittest

from groundwork import progbar as pbmod


class ProgBarTest(unittest.TestCase):
    def test_transition_targets_existing_progress_selectors(self):
        css = pbmod.progbar_css()
        for sel in (".bar i", "#readprogress span"):
            self.assertIn(sel, css)
        self.assertIn("transition", css)
        self.assertIn("width", css)

    def test_total_motion_under_300ms(self):
        css = pbmod.progbar_css()
        durations = [int(m.group(1))
                     for m in re.finditer(r"(\d+)\s*ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLessEqual(ms, 300)

    def test_reduced_motion_override_disables_transition(self):
        css = pbmod.progbar_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("transition:none", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = pbmod.progbar_css().lower()
        self.assertNotIn("<style", css)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "fast", -50, 9999, object()):
            ms = pbmod.transition_ms(bad)
            self.assertGreaterEqual(ms, 0)
            self.assertLessEqual(ms, 300)
        self.assertEqual(pbmod.selectors(), (".bar i", "#readprogress span"))

    def test_section_html_anchor(self):
        html = pbmod.section_html()
        self.assertIn("id='status-b10-progbar'", html)


if __name__ == "__main__":
    unittest.main()
