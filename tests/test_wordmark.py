"""Inline SVG wordmark for header and module exports (I-55)."""
import unittest

from groundwork import wordmark as wmmod


class WordmarkTest(unittest.TestCase):
    def test_anchor_constant(self):
        self.assertEqual(wmmod.STATUS_ANCHOR, "status-b10-wordmark")

    def test_svg_is_inline_svg_with_currentcolor(self):
        svg = wmmod.wordmark_svg()
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("currentColor", svg)
        self.assertIn("Groundwork", svg)

    def test_svg_has_no_emoji_no_hardcoded_ink_no_network(self):
        svg = wmmod.wordmark_svg()
        # The xmlns namespace identifier is not a network fetch.
        inline = svg.replace("xmlns='http://www.w3.org/2000/svg'", "")
        for marker in ("http://", "https://", "url(", "@import",
                       "<image", "data:image"):
            self.assertNotIn(marker, inline)
        # Painted shapes inherit the palette; no baked-in hex fills.
        self.assertNotIn("fill='#", svg)
        self.assertNotIn('fill="#', svg)
        self.assertFalse(any(ord(c) > 0x2500 for c in svg))

    def test_svg_is_accessible(self):
        svg = wmmod.wordmark_svg()
        self.assertIn("role='img'", svg)
        self.assertIn("aria-label='Groundwork'", svg)
        self.assertIn("<title>Groundwork</title>", svg)

    def test_height_clamps_to_16_32_and_defaults(self):
        self.assertIn("height='16'", wmmod.wordmark_svg(4))
        self.assertIn("height='16'", wmmod.wordmark_svg(-8))
        self.assertIn("height='32'", wmmod.wordmark_svg(200))
        for bad in (None, "tall", object()):
            self.assertIn("height='24'", wmmod.wordmark_svg(bad))

    def test_word_fails_closed_and_escapes(self):
        for bad in ("", None, "   ", 0, 5, ["G"]):
            self.assertIn("Groundwork", wmmod.wordmark_svg(word=bad))
        svg = wmmod.wordmark_svg(word="<b>G</b>")
        self.assertNotIn("<b>G</b>", svg)
        self.assertIn("&lt;b&gt;G&lt;/b&gt;", svg)

    def test_wordmark_svg_never_raises(self):
        for h in (None, "x", [24], object()):
            for w in (None, 5, ["G"], object()):
                self.assertTrue(wmmod.wordmark_svg(h, w).startswith("<svg"))

    def test_css_is_raw_declarations_only(self):
        css = wmmod.wordmark_css()
        self.assertNotIn("<style", css.lower())
        self.assertNotIn("</style", css.lower())
        for rule in (".wordmark{", ".wordmark-sm{", ".wordmark-lg{"):
            self.assertIn(rule, css)
        self.assertIn("height:24px", css)
        self.assertIn("height:16px", css)
        self.assertIn("height:32px", css)

    def test_section_html_anchor(self):
        html = wmmod.section_html()
        self.assertIn("id='status-b10-wordmark'", html)

    def test_section_html_shows_mark(self):
        html = wmmod.section_html()
        self.assertIn("<svg", html)
        self.assertIn("currentColor", html)


if __name__ == "__main__":
    unittest.main()
