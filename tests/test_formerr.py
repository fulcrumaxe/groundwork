"""Inline form validation errors (I-84): alert line beside the field."""
import unittest

from groundwork import formerr as fmod


class FormerrTest(unittest.TestCase):
    def test_valid_confidences_silent(self):
        # "" counts as missing: the server default (3) applies, no error.
        for good in ("1", "3", "5", " 4 ", "", 2, None):
            self.assertEqual(fmod.confidence_error(good), "", good)

    def test_bad_confidences_name_the_fix(self):
        for bad in ("0", "6", "9", "-1", "abc", "3.5"):
            with self.subTest(bad=bad):
                msg = fmod.confidence_error(bad)
                self.assertTrue(msg)
                self.assertIn("1", msg)
                self.assertIn("5", msg)

    def test_never_raises(self):
        for bad in (object(), ["3"], {"c": 1}, float("nan")):
            self.assertIsInstance(fmod.confidence_error(bad), str)
            self.assertIsInstance(
                fmod.field_error_html(bad, bad), str)

    def test_review_note_parses_like_handler(self):
        self.assertEqual(fmod.review_note("answer=x&confidence=4"), "")
        self.assertEqual(fmod.review_note("answer=x"), "")  # default
        self.assertEqual(fmod.review_note(""), "")
        self.assertEqual(fmod.review_note(None), "")
        bad = fmod.review_note("answer=x&confidence=9")
        self.assertIn("field-error", bad)
        self.assertIn("role='alert'", bad)
        self.assertIn("confidence", bad)
        abc = fmod.review_note("confidence=abc")
        self.assertTrue(abc)
        self.assertIn("role='alert'", abc)
        self.assertIsInstance(fmod.review_note(object()), str)

    def test_error_line_shape(self):
        line = fmod.field_error_html("confidence", "pick 1–5")
        self.assertIn("role='alert'", line)
        self.assertIn("field-error", line)
        self.assertIn("<b>confidence:</b>", line)
        evil = fmod.field_error_html("<script>", "<img src=x onerror=y>")
        self.assertNotIn("<script>", evil)
        self.assertNotIn("<img", evil)

    def test_css_raw_declarations_only(self):
        css = fmod.formerr_css()
        self.assertIn(".field-error", css)
        self.assertIn("var(--fail)", css)
        self.assertNotIn("<style", css.lower())

    def test_css_braces_balanced(self):
        # Regression (Batch 13): a stray closer in a plain-string
        # continuation once rode along; every emitter must balance.
        css = fmod.formerr_css()
        self.assertEqual(css.count("{"), css.count("}"))
        # References only real palette tokens.
        self.assertNotIn("--accent", css)

    def test_demo_shows_firing_line(self):
        demo = fmod.demo_html()
        self.assertIn("field-error", demo)
        self.assertIn("role='alert'", demo)
        self.assertIn("field-invalid", demo)

    def test_section_html_anchor(self):
        html = fmod.section_html()
        self.assertIn("id='status-b13-formerr'", html)
        self.assertIn("confidence_error", html)

    def test_tour_entry_shape(self):
        e = fmod.tour_entry()
        self.assertEqual(e, {
            "id": "inline-errors",
            "kind": "improvement",
            "title": "Inline form errors",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-formerr",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "formerr.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
