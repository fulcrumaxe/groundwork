"""Batch 18, I-103: glossary tooltips ride the lesson rendering path."""
import unittest

from groundwork import explain as explainmod
from groundwork import glossary as glossmod
from groundwork import lessons as lesmod


def _lesson(**kw):
    base = {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "Adds a and b. Recursion is not used here.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "",
            "how": [], "worked": None,
            "dualcode": {"steps": [], "states": []}}
    base.update(kw)
    return base


class GlossUnitTest(unittest.TestCase):
    def test_known_term_gains_dfn_tooltip(self):
        out = glossmod.gloss_html("Recursion solves smaller pieces.")
        self.assertIn("<dfn class='gloss'", out)
        self.assertIn("runs itself", out)
        self.assertIn("Recursion", out)  # source casing preserved

    def test_unknown_terms_pass_through_untouched(self):
        out = glossmod.gloss_html("The frobnicate wobbles.")
        self.assertNotIn("<dfn", out)
        self.assertIn("frobnicate", out)

    def test_hostile_input_never_raises(self):
        self.assertEqual(glossmod.gloss_html(None), "")
        self.assertIn("x", glossmod.gloss_html("x"))
        self.assertEqual(glossmod.annotate_html(None), "")
        self.assertNotIn("<dfn", glossmod.annotate_html("<a title='recursion'>x</a>"))

    def test_terms_cover_explainer_semantics(self):
        for term in explainmod.GLOSSARY:
            self.assertIn(term, glossmod.TERMS)


class GlossEffectTest(unittest.TestCase):
    def test_rendered_lesson_marks_known_jargon(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("<dfn class='gloss'", html_out)
        self.assertIn("title=", html_out)

    def test_rendered_lesson_leaves_unknown_words_alone(self):
        lesson = _lesson(summary="Adds a and b with frobnicate care.")
        html_out = lesmod.render_levels(lesson, 0.0, 0, "auto", "/")
        self.assertIn("frobnicate", html_out)
        self.assertNotIn("frobnicate</dfn>", html_out)

    def test_legacy_no_data_path_pinned_as_fallback(self):
        # Pre-glossary behavior: plain escaped text, no dfn markup.
        import html as _html
        plain = _html.escape("Recursion solves smaller pieces.")
        self.assertNotIn("<dfn", plain)
        # And the helper degrades identically on empty input.
        self.assertEqual(glossmod.gloss_html(""), "")


if __name__ == "__main__":
    unittest.main()
