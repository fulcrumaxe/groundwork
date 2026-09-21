"""Subtle Due card entrance stagger, CSS only (I-59)."""
import re
import unittest
from pathlib import Path

from groundwork import stagger as stagmod


class StaggerTest(unittest.TestCase):
    def test_nth_child_delays_present(self):
        css = stagmod.stagger_css()
        self.assertIn("nth-child", css)
        delays = re.findall(r"animation-delay:(\d+)ms", css)
        self.assertGreaterEqual(len(delays), stagmod.MAX_CARDS)

    def test_total_delay_budget_parseable_and_capped(self):
        css = stagmod.stagger_css()
        delays = [int(d) for d in
                  re.findall(r"animation-delay:(\d+)ms", css)]
        self.assertTrue(delays)
        self.assertLessEqual(max(delays), 300)
        self.assertLessEqual(max(delays), stagmod.TOTAL_BUDGET_MS)
        self.assertEqual(stagmod.max_delay_ms(), 245)

    def test_keyframe_duration_under_300ms(self):
        css = stagmod.stagger_css()
        seconds = [float(d) for d in
                   re.findall(r"animation:\S+ (\d+(?:\.\d+)?)s", css)]
        self.assertTrue(seconds)
        for s in seconds:
            self.assertLessEqual(s, 0.3)

    def test_reduced_motion_override_present(self):
        css = stagmod.stagger_css()
        self.assertIn("prefers-reduced-motion", css)
        head, _, tail = css.partition("prefers-reduced-motion")
        self.assertIn("animation:none", tail.replace(" ", ""))

    def test_no_tag_or_script_literals(self):
        css = stagmod.stagger_css()
        html = stagmod.section_html()
        for blob in (css, html):
            lowered = blob.lower()
            self.assertNotIn("<style", lowered)
            self.assertNotIn("<script", lowered)
        src = Path(__file__).resolve().parent.parent.joinpath(
            "groundwork", "stagger.py").read_text(encoding="utf-8")
        lowered = src.lower()
        self.assertNotIn("<style", lowered)
        self.assertNotIn("<script", lowered)
        for marker in ("document.", "addeventlistener", "settimeout"):
            self.assertNotIn(marker, lowered)

    def test_base_keyframe_rule_present(self):
        css = stagmod.stagger_css()
        self.assertIn("@keyframes", css)
        self.assertIn("#queue", css)
        self.assertIn("article", css)

    def test_cap_rule_pins_deep_cards(self):
        css = stagmod.stagger_css()
        self.assertIn(f"nth-child(n+{stagmod.MAX_CARDS + 2})", css)

    def test_delay_helpers_fail_closed_never_raise(self):
        self.assertEqual(stagmod.delay_for(1), 0)
        self.assertEqual(stagmod.delay_for(2), stagmod.STEP_MS)
        for bad in (0, -3, "", None, object(), "soon"):
            self.assertEqual(stagmod.delay_for(bad), 0)
        self.assertIsInstance(stagmod.stagger_css(), str)

    def test_section_html_anchor(self):
        html = stagmod.section_html()
        self.assertIn("id='status-b10-stagger'", html)


if __name__ == "__main__":
    unittest.main()
