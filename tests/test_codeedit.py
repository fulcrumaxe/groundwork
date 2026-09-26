"""Real code editor (I-154): caller effect + legacy fallback pinned."""
import unittest

from groundwork import cards as cardsmod
from groundwork import codeedit as cemod


def _code_card(etype="12"):
    return {"id": "7", "exercise_type": etype, "payload": "{}"}


class CodeTypeTest(unittest.TestCase):
    def test_code_branches(self):
        for etype in ("12", "14", "19", "20", "23", 12):
            self.assertTrue(cemod.is_code_type(etype))

    def test_non_code_and_bad(self):
        for etype in ("1", "5", "8", None, object()):
            self.assertFalse(cemod.is_code_type(etype))


class LineCountTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(cemod.line_count("a\nb\nc"), 3)
        self.assertEqual(cemod.line_count("one"), 1)

    def test_empty_and_bad(self):
        self.assertEqual(cemod.line_count(""), 0)
        self.assertEqual(cemod.line_count(None), 0)
        self.assertEqual(cemod.line_count(12345), 1)


class EditorHtmlTest(unittest.TestCase):
    def test_posts_answer_field(self):
        body = cemod.editor_html("x = 1")
        self.assertIn("name='answer'", body)
        self.assertIn("class='codeedit-input'", body)
        self.assertIn("<textarea", body)
        self.assertNotIn("contenteditable", body)

    def test_gutter_matches_lines(self):
        body = cemod.editor_html("a\nb\nc")
        self.assertIn("<span>1</span><span>2</span><span>3</span>", body)
        self.assertIn("aria-hidden='true'", body)

    def test_escapes_code(self):
        body = cemod.editor_html("<script>alert(1)</script>")
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>alert", body)

    def test_empty_and_none_fallback(self):
        for bad in (None, "", object()):
            body = cemod.editor_html(bad)
            self.assertIn("<textarea", body)
            self.assertIn("name='answer'", body)

    def test_editor_id_anchor(self):
        body = cemod.editor_html("x", editor_id="codeedit")
        self.assertIn("id='codeedit'", body)
        self.assertNotIn("id=''", cemod.editor_html("x"))


class CssJsTest(unittest.TestCase):
    def test_mono_font(self):
        css = cemod.editor_css()
        self.assertIn("monospace", css)
        self.assertIn("codeedit-gutter", css)
        self.assertIn("user-select:none", css.replace(" ", ""))
        # Rules only: joins inside the single head sheet, never nested.
        self.assertNotIn("<style>", css)
        self.assertNotIn("</style>", css)

    def test_tab_handling(self):
        js = cemod.editor_js()
        self.assertIn("Tab", js)
        self.assertIn("preventDefault", js)
        self.assertIn("shiftKey", js)
        self.assertIn("codeeditSync", js)
        self.assertIn("__codeeditInit", js)

    def test_never_raises(self):
        self.assertIn(".codeedit", cemod.editor_css())
        self.assertTrue(cemod.editor_js().startswith("<"))


class SectionTest(unittest.TestCase):
    def test_anchor(self):
        body = cemod.section_html()
        self.assertIn(f"id='{cemod.STATUS_ANCHOR}'", body)
        self.assertIn("codeedit", body)


class EffectTest(unittest.TestCase):
    def test_caller_widget_renders_editor(self):
        body = cardsmod.answer_widget(_code_card())
        self.assertIn("codeedit-input", body)
        self.assertIn("codeedit-gutter", body)
        # Posting contract unchanged: the review POST still gets answer.
        self.assertIn("name='answer'", body)
        self.assertIn("action='/cards/7/review'", body)

    def test_non_code_cards_untouched(self):
        body = cardsmod.answer_widget(_code_card("1"))
        self.assertNotIn("codeedit-input", body)

    def test_legacy_fallback_pinned(self):
        # No-JS rendering is a real textarea posting answer: grade path
        # sees the same field it always did.
        body = cemod.editor_html(None)
        self.assertIn("<textarea", body)
        self.assertIn("name='answer'", body)


if __name__ == "__main__":
    unittest.main()
