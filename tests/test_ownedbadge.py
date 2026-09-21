"""Celebrate Owned status with a non-emoji badge reveal (I-58)."""
import re
import unittest

from groundwork import ownedbadge as badgemod


class OwnedBadgeTest(unittest.TestCase):
    def test_keyframes_present(self):
        css = badgemod.badge_css()
        self.assertIn("@keyframes ownedbadge-reveal", css)
        self.assertIn("from{", css)
        self.assertIn("to{", css)
        self.assertIn("opacity:1", css)

    def test_no_style_tags(self):
        # Raw declarations only: the parent owns the head <style> wire
        # (see web.py CSS concat); a nested tag would close it early.
        css = badgemod.badge_css().lower()
        self.assertNotIn("<style", css)
        self.assertNotIn("</style", css)

    def test_no_emoji_or_non_ascii_in_css(self):
        css = badgemod.badge_css()
        self.assertTrue(css.isascii())
        for glyph in ("🏆", "🎉", "⭐", "✅", "✓", "★"):
            self.assertNotIn(glyph, css)

    def test_reduced_motion_override_present(self):
        css = badgemod.badge_css()
        self.assertIn("prefers-reduced-motion", css)
        media = css.split("prefers-reduced-motion", 1)[1]
        self.assertIn("animation:none", media)
        self.assertIn("opacity:1", media)
        self.assertIn("transform:none", media)

    def test_total_motion_under_300ms(self):
        css = badgemod.badge_css()
        durations = [int(m) for m in re.findall(r"(\d+)ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLess(ms, 300)
        self.assertIn("240ms", css)

    def test_owned_vs_plain_class(self):
        self.assertEqual(badgemod.badge_class("Owned"), "chip owned-badge")
        self.assertEqual(badgemod.badge_class("  owned "), "chip owned-badge")
        self.assertEqual(badgemod.badge_class("New"), "chip")
        self.assertEqual(badgemod.badge_class("Stale"), "chip")

    def test_badge_html_owned_carries_reveal(self):
        html = badgemod.badge_html("Owned")
        self.assertIn("owned-badge", html)
        self.assertIn("Owned", html)
        self.assertIn("data-status='Owned'", html)

    def test_badge_html_escapes_non_owned(self):
        html = badgemod.badge_html("<script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("class='chip'", html)

    def test_helpers_fail_closed_never_raise(self):
        for bad in ("", None, 5, ["Owned"], object()):
            self.assertEqual(badgemod.badge_class(bad), "chip")
            self.assertIsInstance(badgemod.badge_html(bad), str)
        self.assertIsInstance(badgemod.badge_css(), str)
        self.assertIsInstance(badgemod.section_html(), str)

    def test_section_html_anchor(self):
        html = badgemod.section_html()
        self.assertIn("id='status-b10-ownedbadge'", html)
        self.assertIn("badge_css", html)


if __name__ == "__main__":
    unittest.main()
