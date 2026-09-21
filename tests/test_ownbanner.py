"""Confetti-free Owned celebration banner (I-79)."""
import re
import unittest

from groundwork import ownbanner as obmod


class OwnBannerTest(unittest.TestCase):
    def test_name_escaping(self):
        html = obmod.ownbanner_html("<script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("role='status'", html)
        self.assertIn("ownbanner", html)

    def test_empty_name_fails_closed(self):
        for bad in ("", None, 5, ["x"], object()):
            html = obmod.ownbanner_html(bad)
            self.assertIsInstance(html, str)
            self.assertIn("ownbanner", html)
            self.assertIn("taken root", html)

    def test_no_emoji_ascii_only(self):
        html = obmod.ownbanner_html("Loops")
        css = obmod.ownbanner_css()
        for blob in (html, css):
            self.assertTrue(blob.isascii())
            for glyph in ("🏆", "🎉", "⭐", "✅", "✓", "★", "🌱", "🌳"):
                self.assertNotIn(glyph, blob)

    def test_motion_budget_max_250ms(self):
        css = obmod.ownbanner_css()
        durations = [int(m) for m in re.findall(r"(\d+)ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLessEqual(ms, 250)
        self.assertIn(f"{obmod.FADE_MS}ms", css)

    def test_reduced_motion_gate(self):
        css = obmod.ownbanner_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        media = css.split("prefers-reduced-motion", 1)[1]
        self.assertIn("animation:none", media)
        self.assertIn("opacity:1", media)

    def test_uses_real_palette_tokens(self):
        css = obmod.ownbanner_css()
        self.assertIn("var(--ink", css)
        self.assertIn("var(--paper", css)
        self.assertNotIn("var(--accent,", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = obmod.ownbanner_css().lower()
        self.assertNotIn("<style", css)
        self.assertNotIn("</style", css)

    def test_composes_with_ownedbadge_vocabulary(self):
        html = obmod.ownbanner_html("Loops")
        self.assertIn("chip owned-badge", html)
        css = obmod.ownbanner_css()
        self.assertNotIn("ownedbadge-reveal", css)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "fast", -50, 9999, object()):
            ms = obmod.fade_ms(bad)
            self.assertGreaterEqual(ms, 0)
            self.assertLessEqual(ms, 250)
        self.assertIsInstance(obmod.ownbanner_css(), str)
        self.assertIsInstance(obmod.section_html(), str)
        self.assertIsInstance(obmod.tour_entry(), dict)

    def test_section_html_anchor(self):
        html = obmod.section_html()
        self.assertIn("id='status-b12-ownbanner'", html)
        self.assertIn("ownbanner_css", html)

    def test_tour_entry_shape(self):
        e = obmod.tour_entry()
        self.assertEqual(e["id"], "owned-banner")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["title"], "Owned banner")
        self.assertTrue(e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-ownbanner")


if __name__ == "__main__":
    unittest.main()
