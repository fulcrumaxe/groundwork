"""Selection accent (I-85): ::selection on the real accent token."""
import unittest

from groundwork import selection as selmod


class SelectionTest(unittest.TestCase):
    def test_rule_uses_real_tokens(self):
        css = selmod.selection_css()
        self.assertIn("::selection", css)
        self.assertIn("var(--accent-due)", css)
        self.assertIn("var(--ink)", css)
        # Batch 12 correction: no generic --accent exists.
        self.assertNotIn("var(--accent)", css.replace(
            "var(--accent-due)", ""))
        self.assertNotIn("<style", css.lower())

    def test_forced_colors_escape(self):
        css = selmod.selection_css().replace(" ", "")
        self.assertIn("forced-colors", css)
        self.assertIn("Highlight", css)

    def test_section_html_anchor(self):
        html = selmod.section_html()
        self.assertIn("id='status-b13-selection'", html)
        self.assertIn("selection_css", html)

    def test_tour_entry_shape(self):
        e = selmod.tour_entry()
        self.assertEqual(e, {
            "id": "selection-accent",
            "kind": "improvement",
            "title": "Selection accent",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-selection",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "selection.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
