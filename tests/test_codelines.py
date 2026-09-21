"""Line numbers for code blocks sharing the Batch 1 copy button (I-61)."""
import unittest

from groundwork import codelines as codemod


class CodeLinesTest(unittest.TestCase):
    def test_anchor_constant(self):
        self.assertEqual(codemod.STATUS_ANCHOR, "status-b10-codelines")

    def test_counter_rules_present(self):
        css = codemod.codelines_css()
        self.assertIsInstance(css, str)
        self.assertIn("counter-reset", css)
        self.assertIn("counter-increment", css)
        self.assertIn("counter(codeline)", css)

    def test_counters_target_pre_and_code_selectors(self):
        css = codemod.codelines_css()
        self.assertIn("pre", css)
        self.assertIn("code", css)
        # Reset lives on the block, increment on the per-line hook.
        self.assertLess(css.index("pre{counter-reset"),
                        css.index("counter-increment"))

    def test_no_style_or_script_literals(self):
        blob = codemod.codelines_css() + codemod.section_html()
        self.assertNotIn("<style", blob)
        self.assertNotIn("<script", blob)

    def test_graceful_degradation(self):
        css = codemod.codelines_css()
        # Numbers live only in generated content; code text is never hidden.
        self.assertIn("::before", css)
        self.assertIn("content:counter(codeline)", css)
        self.assertNotIn("display:none", css)
        # Gutter skips selection so copies stay clean.
        self.assertIn("user-select:none", css)

    def test_no_competing_copy_button(self):
        css = codemod.codelines_css()
        self.assertNotIn("copybtn", css)
        self.assertNotIn("Copy", css)
        html = codemod.section_html()
        # Documents the pre-existing button as the same unit instead.
        self.assertIn("Copy", html)

    def test_numbered_html_wraps_each_line(self):
        out = codemod.numbered_html("a\nb")
        self.assertEqual(out.count("class='codeline'"), 2)
        self.assertIn(">a<", out)
        self.assertIn(">b<", out)

    def test_numbered_html_escapes(self):
        out = codemod.numbered_html("<b>x</b>")
        self.assertNotIn("<b>x</b>", out)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", out)

    def test_numbered_html_preserves_text(self):
        # Spans must not change the copied characters.
        code = "def f():\n    return 1"
        out = codemod.numbered_html(code)
        self.assertEqual(out.replace("<span class='codeline'>", "")
                         .replace("</span>", ""), code)

    def test_line_count(self):
        self.assertEqual(codemod.line_count("a\nb\nc"), 3)
        self.assertEqual(codemod.line_count("one"), 1)
        self.assertEqual(codemod.line_count(""), 0)

    def test_helpers_fail_closed_never_raise(self):
        # None/"" have no lines; other scalars coerce to their one-line
        # repr (readtime._words precedent) — never raise either way.
        self.assertEqual(codemod.line_count(None), 0)
        self.assertEqual(codemod.numbered_html(None), "")
        self.assertEqual(codemod.numbered_html(""), "")
        for bad in (5, ["x"], object(), {"n": 1}):
            self.assertGreaterEqual(codemod.line_count(bad), 1)
            self.assertIn("codeline", codemod.numbered_html(bad))
        self.assertEqual(codemod._safe_text(None), "")
        self.assertIsInstance(codemod.codelines_css(), str)
        self.assertIsInstance(codemod.section_html(), str)

    def test_section_html_anchor(self):
        html = codemod.section_html()
        self.assertIn("id='status-b10-codelines'", html)


if __name__ == "__main__":
    unittest.main()
