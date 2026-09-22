"""Collapse long source blocks (I-108)."""
import unittest

from groundwork import codelines as codemod
from groundwork import lessons as lesmod
from groundwork import srccollapse as srcmod


def _long(n=30):
    return "\n".join(f"line {i}: x = {i}" for i in range(n))


class ThresholdTest(unittest.TestCase):
    def test_short_is_not_long(self):
        self.assertFalse(srcmod.is_long("a\nb"))
        self.assertFalse(
            srcmod.is_long("\n".join(["x"] * srcmod.MAX_VISIBLE_LINES)))

    def test_long_is_long(self):
        self.assertTrue(srcmod.is_long(_long()))

    def test_bad_input_fails_closed(self):
        self.assertFalse(srcmod.is_long(None))
        self.assertFalse(srcmod.is_long(""))
        self.assertEqual(srcmod.line_count(None), 0)
        self.assertEqual(srcmod.block_html(None), "")
        self.assertEqual(srcmod.block_html(""), "")


class LegacyByteIdenticalTest(unittest.TestCase):
    def test_short_block_is_legacy_pre(self):
        code = "def f():\n    return 1"
        self.assertEqual(srcmod.block_html(code),
                         f"<pre>{codemod.numbered_html(code)}</pre>")

    def test_short_block_preserves_copy_text(self):
        code = "def f():\n    return 1"
        out = srcmod.block_html(code)
        self.assertEqual(out.replace("<span class='codeline'>", "")
                         .replace("</span>", "").replace("<pre>", "")
                         .replace("</pre>", ""), code)


class CollapseWidgetTest(unittest.TestCase):
    def test_long_block_expands_with_summary(self):
        out = srcmod.block_html(_long(30))
        self.assertIn("<details", out)
        self.assertIn("Show full file context", out)
        self.assertIn("30 lines", out)
        self.assertNotIn("open",
                         out.split("<details", 1)[1].split(">", 1)[0])

    def test_long_block_keeps_full_text_and_escapes(self):
        code = _long(20) + "\n<evil>&"
        out = srcmod.block_html(code)
        self.assertNotIn("<evil>", out)
        self.assertIn("&lt;evil&gt;", out)
        self.assertEqual(out.count("class='codeline'"), 21 + 8)

    def test_no_script_style_or_ids(self):
        out = srcmod.block_html(_long(30))
        self.assertNotIn("<script", out)
        self.assertNotIn("<style", out)
        self.assertNotIn("id=", out)

    def test_never_raises(self):
        for bad in (5, ["x"], object(), {"n": 1}):
            self.assertIsInstance(srcmod.block_html(bad), str)


class CallerEffectTest(unittest.TestCase):
    def _lesson(self, source):
        return {"name": "f", "kind": "function", "file": "a.py",
                "line": 1, "summary": "does f",
                "how": ["step one"], "source": source,
                "docstring": "", "callers": [], "callees": []}

    def test_long_source_collapses_on_lesson_page(self):
        # The Source pre block renders at L3; the L2 predict cover is
        # untouched by collapse by design.
        html_out = lesmod.render_levels(
            self._lesson(_long(30)), 0.0, 0, "3", "/m/1")
        self.assertIn("Show full file context", html_out)

    def test_short_source_renders_legacy_bytes(self):
        code = "def f():\n    return 1"
        html_out = lesmod.render_levels(
            self._lesson(code), 0.0, 0, "3", "/m/1")
        self.assertIn(f"<pre>{codemod.numbered_html(code)}</pre>", html_out)
        self.assertNotIn("Show full file context", html_out)

    def test_missing_source_has_no_expander(self):
        html_out = lesmod.render_levels(
            self._lesson(""), 0.0, 0, "3", "/m/1")
        self.assertNotIn("Show full file context", html_out)


class StatusTourTest(unittest.TestCase):
    def test_anchor_and_tour(self):
        self.assertEqual(srcmod.STATUS_ANCHOR, "status-b19-srccollapse")
        self.assertIn(f"id='{srcmod.STATUS_ANCHOR}'",
                      srcmod.section_html())
        e = srcmod.tour_entry()
        self.assertEqual(e["anchor"], "{lesson}")


if __name__ == "__main__":
    unittest.main()
