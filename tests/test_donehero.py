"""Session-complete hero for empty Due (I-70)."""
import unittest

from groundwork import donehero as dhmod


class DoneHeroTest(unittest.TestCase):
    def test_svg_currentcolor_no_emoji(self):
        svg = dhmod.hero_svg()
        self.assertIn("currentColor", svg)
        self.assertIn("role='img'", svg)
        self.assertIn("<title>", svg)
        self.assertTrue(svg.isascii())
        for glyph in ("\U0001f3c6\U0001f389\U00002b50\U00002705\U00002713\U00002605"):
            self.assertNotIn(glyph, svg)
        self.assertNotIn("<text", svg)
        self.assertNotIn("animate", svg)
        self.assertNotIn("confetti", svg)

    def test_css_no_style_tags_no_keyframes(self):
        css = dhmod.hero_css()
        self.assertNotIn("<style", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertNotIn("@keyframes", css)

    def test_counts_coerced(self):
        out = dhmod.done_hero_html(-2, 140, "")
        self.assertIn("0 answered", out)
        self.assertIn("100%", out)
        out = dhmod.done_hero_html("3", "bad", None)
        self.assertIn("3 answered", out)
        self.assertIn("0%", out)

    def test_next_due_escaped(self):
        out = dhmod.done_hero_html(1, 50, "<script>")
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)

    def test_anchor_and_links(self):
        out = dhmod.done_hero_html()
        self.assertIn("id='done-hero'", out)
        self.assertIn("<a href='/modules'", out)
        self.assertIn("All caught up", out)

    def test_never_raises(self):
        for bad in ("", None, 5, ["x"], object()):
            self.assertIsInstance(dhmod.hero_svg(), str)
            self.assertIsInstance(
                dhmod.done_hero_html(bad, bad, bad), str)
            self.assertIsInstance(dhmod.hero_css(), str)
        self.assertIn("status-b11-donehero", dhmod.section_html())


if __name__ == "__main__":
    unittest.main()
