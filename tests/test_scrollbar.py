"""Platform-respecting scrollbars (I-86): thin, palette-matched, escapable."""
import unittest

from groundwork import scrollbar as sbmod


class ScrollbarTest(unittest.TestCase):
    def test_covers_both_engines(self):
        css = sbmod.scrollbar_css()
        self.assertIn("scrollbar-width:thin", css.replace(" ", ""))
        self.assertIn("scrollbar-color", css)
        self.assertIn("::-webkit-scrollbar", css)
        self.assertIn("::-webkit-scrollbar-thumb", css)
        self.assertNotIn("<style", css.lower())

    def test_real_tokens_only(self):
        css = sbmod.scrollbar_css()
        self.assertIn("var(--stale)", css)
        self.assertIn("var(--paper)", css)
        self.assertNotIn("var(--accent)", css.replace(
            "var(--accent-due)", ""))

    def test_platform_opt_outs(self):
        css = sbmod.scrollbar_css().replace(" ", "")
        # Touch devices keep full-size scrolling; forced-colors
        # (high contrast) keeps native scrollbars.
        self.assertIn("pointer:coarse", css)
        self.assertIn("scrollbar-width:auto", css)
        self.assertIn("forced-colors", css)
        self.assertIn("scrollbar-color:auto", css)

    def test_section_html_anchor(self):
        html = sbmod.section_html()
        self.assertIn("id='status-b13-scrollbar'", html)
        self.assertIn("scrollbar_css", html)

    def test_tour_entry_shape(self):
        e = sbmod.tour_entry()
        self.assertEqual(e, {
            "id": "palette-scrollbars",
            "kind": "improvement",
            "title": "Palette scrollbars",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-scrollbar",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "scrollbar.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
