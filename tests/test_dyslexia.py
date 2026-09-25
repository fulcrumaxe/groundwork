"""Dyslexia-friendly type/spacing toggle (I-139)."""
import unittest

from groundwork import dyslexia as mod
from groundwork import web as webmod


class ToggleTest(unittest.TestCase):
    def test_css_scopes_to_attr(self):
        css = mod.dyslexia_css()
        self.assertIn("data-dys='on'", css.replace('"', "'"))
        self.assertIn("line-height:1.75", css)
        self.assertIn("letter-spacing", css)
        self.assertIn("word-spacing", css)
        self.assertIn(f"#{mod.TOGGLE_ID}", css)

    def test_js_persists_and_toggles(self):
        js = mod.toggle_js()
        self.assertIn("data-dys-toggle", js)
        self.assertIn(mod.STORE_KEY, js)
        self.assertIn("localStorage", js)
        self.assertIn("setAttribute", js)
        self.assertIn("removeAttribute", js)

    def test_button_shape(self):
        body = mod.toggle_html()
        self.assertIn(f"id='{mod.TOGGLE_ID}'", body)
        self.assertIn("Readable", body)

    def test_default_off_without_js(self):
        raw = webmod.page("T", "<p>x</p>").decode()
        self.assertIn("<html><head>", raw)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "dyslexia-toggle", "kind": "improvement",
            "title": "Dyslexia-friendly reading",
            "blurb": ("One header button widens spacing and line-height "
                      "— reading stays comfortable."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_every_page_carries_toggle(self):
        raw = webmod.page("T", "<p>x</p>").decode()
        self.assertIn(f"id='{mod.TOGGLE_ID}'", raw)
        self.assertIn("data-dys-toggle", raw)
        self.assertIn("line-height:1.75", raw)


if __name__ == "__main__":
    unittest.main()
