"""Tiny dependency-free Python/TS syntax highlight (I-62)."""
import unittest

from groundwork import highlight as hlmod


class HighlightTest(unittest.TestCase):
    def test_anchor_constant(self):
        self.assertEqual(hlmod.STATUS_ANCHOR, "status-b10-highlight")

    def test_python_keywords_wrapped(self):
        out = hlmod.highlight_html("def foo():\n    return 1", "python")
        self.assertIn("<span class='tok-keyword'>def</span>", out)
        self.assertIn("<span class='tok-keyword'>return</span>", out)

    def test_python_strings_comments_numbers(self):
        out = hlmod.highlight_html("x = 'hi'  # greet\nn = 0x1F", "python")
        self.assertIn("<span class='tok-string'>&#x27;hi&#x27;</span>", out)
        self.assertIn("<span class='tok-comment'># greet</span>", out)
        self.assertIn("<span class='tok-number'>0x1F</span>", out)

    def test_python_prefix_and_fstring(self):
        toks = dict()
        for kind, text in hlmod.tokenize("rf'{a}b' + r'\\d'", "python"):
            toks.setdefault(kind, []).append(text)
        self.assertEqual("".join(toks.get("string", [])), "rf'{a}b'r'\\d'")

    def test_ts_template_literal_handled(self):
        out = hlmod.highlight_html("const s = `hi ${name}`;", "ts")
        self.assertIn("<span class='tok-keyword'>const</span>", out)
        self.assertIn("tok-string", out)
        self.assertIn("hi ${name}", out.replace("&#x27;", "'"))

    def test_ts_comments_and_typescript_alias(self):
        a = hlmod.highlight_html("// line\n/* block */\nlet x = 2;", "ts")
        b = hlmod.highlight_html("// line\n/* block */\nlet x = 2;",
                                 "typescript")
        self.assertEqual(a, b)
        self.assertIn("<span class='tok-comment'>// line</span>", a)
        self.assertIn("<span class='tok-comment'>/* block */</span>", a)
        self.assertIn("<span class='tok-keyword'>let</span>", a)

    def test_escape_intactness(self):
        evil = "<script>alert('x')</script> & <b>bold</b>"
        out = hlmod.highlight_html(evil, "python")
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("&amp;", out)
        for raw in ("<script>", "</script>", "<b>", " & "):
            self.assertNotIn(raw, out)

    def test_unknown_lang_passthrough(self):
        self.assertEqual(hlmod.tokenize("x = 1", "ruby"),
                         [("plain", "x = 1")])
        out = hlmod.highlight_html("x = 1", "ruby")
        self.assertNotIn("<span", out)
        self.assertIn("x = 1", out)

    def test_tokenize_lossless(self):
        code = "def f(a=3.14):  # pi\n    return f'v{a}'\n"
        toks = hlmod.tokenize(code, "python")
        self.assertTrue(toks)
        for kind, text in toks:
            self.assertIn(kind, hlmod.KINDS)
            self.assertIsInstance(text, str)
        self.assertEqual("".join(t for _, t in toks), code)

    def test_never_raises_fuzz(self):
        bad_codes = [None, 0, 12345, "", [], {}, "…é…",
                     "unterminated 'string # oops", "/* never closed",
                     "\x00\x01", "f'''\nno end"]
        bad_langs = ["python", "ts", "typescript", "py", "Klingon",
                     "", None, 123, ["ts"]]
        for code in bad_codes:
            for lang in bad_langs:
                toks = hlmod.tokenize(code, lang)
                self.assertIsInstance(toks, list)
                self.assertTrue(toks)
                out = hlmod.highlight_html(code, lang)
                self.assertIsInstance(out, str)
                self.assertIn("<pre class='hl'><code>", out)

    def test_css_declarations_only_with_dark(self):
        css = hlmod.highlight_css()
        self.assertNotIn("<style", css.lower())
        for cls in ("tok-keyword", "tok-string", "tok-comment",
                    "tok-number", "tok-builtin"):
            self.assertIn(cls, css)
        self.assertIn("prefers-color-scheme", css)
        self.assertNotIn("font-family", css)

    def test_section_html_anchor(self):
        html = hlmod.section_html()
        self.assertIn("id='status-b10-highlight'", html)
        self.assertIn("tok-keyword", html)  # live demo rendered inline


if __name__ == "__main__":
    unittest.main()
