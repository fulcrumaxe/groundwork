"""Whole-card clickable module cards (I-16)."""
import unittest

from groundwork import clickcards as ccmod


class ClickcardsTest(unittest.TestCase):
    def test_wrap_card_single_link(self):
        out = ccmod.wrap_card("<h3>Intro</h3>", "/modules/abc", "Open Intro")
        self.assertEqual(out.count("<a "), 1)
        self.assertIn("href='/modules/abc'", out)
        self.assertIn("stretched-link", out)

    def test_nested_links_flattened_not_nested(self):
        inner = "<h3>T</h3><p><a class='btn' href='/modules/abc'>Resume</a></p>"
        out = ccmod.wrap_card(inner, "/modules/abc")
        self.assertEqual(out.count("<a "), 1)
        self.assertIn("Resume", out)
        self.assertNotIn("class='btn'", out)

    def test_href_and_label_escaped(self):
        # "&" is kept by safe_href and escaped at render; "<" falls back.
        out = ccmod.wrap_card("<h3>T</h3>", "/modules/a&b", "<Go>")
        self.assertIn("href='/modules/a&amp;b'", out)
        self.assertIn("&lt;Go&gt;", out)
        self.assertNotIn("<Go>", out)
        back = ccmod.wrap_card("<h3>T</h3>", "/modules/<bad>", "T")
        self.assertIn("href='/modules'", back)
        self.assertNotIn("<bad>", back)

    def test_unsafe_href_falls_back(self):
        for bad in ("https://evil.example/", "javascript:alert(1)", "//evil", ""):
            out = ccmod.wrap_card("inner", bad)
            self.assertIn("href='/modules'", out)

    def test_focus_css_present(self):
        css = ccmod.focus_css()
        self.assertIn("<style>", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("var(--accent-modules", css)
        self.assertIn("outline", css)

    def test_section_anchor_present(self):
        self.assertIn("id='status-b7-clickcards'", ccmod.section_html())

    def test_bad_input_never_raises(self):
        for bad_inner in (None, 123, ["x"], {"h": 1}):
            for bad_href in (None, 0, ["x"], {"h": 1}):
                out = ccmod.wrap_card(bad_inner, bad_href, None)
                self.assertEqual(out.count("<a "), 1)
        self.assertIn("<style>", ccmod.focus_css())

    def test_pure_no_db(self):
        self.assertNotIn("dbmod", dir(ccmod))


if __name__ == "__main__":
    unittest.main()
