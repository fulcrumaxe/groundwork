"""Prediction-then-reveal (F-64): struggle first, read second."""
import unittest

from groundwork import predict as prmod


class PredictTest(unittest.TestCase):
    def test_cover_hides_snippet_no_js(self):
        widget = prmod.cover_html("print(1 + 1)")
        self.assertTrue(prmod.is_covered(widget))
        self.assertIn("<details", widget)
        self.assertIn("<summary>", widget)
        self.assertIn("Predict", widget)
        self.assertIn("<pre", widget)
        self.assertNotIn("<script", widget.lower())
        self.assertNotIn("open", widget.split(">")[0])

    def test_code_escaped_language_scrubbed(self):
        widget = prmod.cover_html("<b>x</b> & 'y'", "<img src=x>")
        self.assertNotIn("<b>x</b>", widget)
        self.assertIn("&lt;b&gt;", widget)
        self.assertNotIn("<img", widget)
        self.assertIn("data-lang='python'", widget)
        self.assertIn("data-lang='rust'",
                       prmod.cover_html("let x = 1;", "rust"))

    def test_empty_code_renders_nothing(self):
        for bad in ("", "   ", None, 42):
            self.assertEqual(prmod.cover_html(bad), "")

    def test_is_covered_rejects_wrong_shapes(self):
        self.assertFalse(prmod.is_covered(""))
        self.assertFalse(prmod.is_covered("<pre>x</pre>"))
        self.assertFalse(prmod.is_covered(
            "<details open><summary>s</summary><pre>x</pre></details>"))
        self.assertFalse(prmod.is_covered(
            "<details><summary>s</summary></details>"))
        self.assertFalse(prmod.is_covered(None))
        self.assertFalse(prmod.is_covered(
            "<details><summary>s</summary><pre>a</pre><pre>b</pre></details>"))

    def test_section_html_anchor(self):
        html = prmod.section_html()
        self.assertIn("id='status-b13-predict'", html)
        self.assertIn("cover_html", html)
        self.assertIn("<details", html)

    def test_tour_entry_shape(self):
        e = prmod.tour_entry()
        self.assertEqual(e, {
            "id": "predict-reveal",
            "kind": "feature",
            "title": "Predict-then-reveal",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-predict",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "predict.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
