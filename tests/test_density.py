"""Compact density toggle (I-89): denser page on demand."""
import re
import unittest

from groundwork import density as dmod


class DensityTest(unittest.TestCase):
    def test_css_overrides_real_tokens_downward(self):
        css = dmod.density_css()
        nospace = css.replace(" ", "")
        self.assertIn("data-density", css)
        for tok in ("--sp-section", "--sp-snug", "--fs-small",
                    "--r-control", "--stale", "--paper", "--ink"):
            self.assertIn(tok, css, tok)
        # Compact shrinks: section gap under the 1rem default, and the
        # tap-target floor is never overridden.
        m = re.search(r"--sp-section:([\d.]+)rem", nospace)
        self.assertTrue(m and float(m.group(1)) < 1.0)
        self.assertNotIn("--tap-min", css)
        self.assertNotIn("<style", css.lower())

    def test_js_persists_without_server(self):
        js = dmod.toggle_js()
        self.assertIn("localStorage", js)
        self.assertIn("data-density", js)
        self.assertIn(dmod.TOGGLE_ID, js)
        self.assertIn("addEventListener", js)
        for banned in ("fetch(", "XMLHttpRequest", "cookie",
                       "preventDefault"):
            self.assertNotIn(banned, js)

    def test_button_matches_js_hook(self):
        btn = dmod.toggle_html()
        self.assertIn(f"id='{dmod.TOGGLE_ID}'", btn)
        self.assertIn("type='button'", btn)
        self.assertIn(dmod.TOGGLE_ID, dmod.toggle_js())
        # Section demo carries a live toggle.
        self.assertIn(f"id='{dmod.TOGGLE_ID}'", dmod.section_html())

    def test_section_html_anchor(self):
        html = dmod.section_html()
        self.assertIn("id='status-b13-density'", html)
        self.assertIn("density_css", html)
        self.assertIn("toggle_js", html)

    def test_tour_entry_shape(self):
        e = dmod.tour_entry()
        self.assertEqual(e, {
            "id": "density-toggle",
            "kind": "improvement",
            "title": "Compact density",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-density",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "density.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
