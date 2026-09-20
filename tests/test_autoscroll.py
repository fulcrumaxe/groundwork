"""Verdict auto-scroll onto the result screen (I-30)."""
import unittest

from groundwork import autoscroll as amod


class VerdictTagTest(unittest.TestCase):
    def test_open_has_verdict_id_and_tabindex(self):
        out = amod.verdict_open(True)
        self.assertIn("id='verdict'", out)
        self.assertIn("tabindex='-1'", out)
        self.assertIn("verdict ok", out)

    def test_open_failed_class(self):
        self.assertIn("verdict stale", amod.verdict_open(False))

    def test_block_escapes_feedback(self):
        out = amod.verdict_block(False, "<script>alert(1)</script>")
        self.assertIn("id='verdict'", out)
        self.assertNotIn("<script>alert", out)
        self.assertIn("&lt;script&gt;", out)

    def test_block_nonstring_feedback(self):
        self.assertIn("42", amod.verdict_block(True, 42))
        self.assertIn("id='verdict'", amod.verdict_block(True, None))


class EnhanceTest(unittest.TestCase):
    def test_injects_anchor(self):
        out = amod.enhance_result("<p class='verdict ok'>done</p>")
        self.assertIn("id='verdict'", out)
        self.assertIn("tabindex='-1'", out)
        self.assertIn("class='verdict ok'", out)

    def test_idempotent(self):
        once = amod.enhance_result("<p class='verdict ok'>done</p>")
        self.assertEqual(amod.enhance_result(once), once)
        self.assertEqual(once.count("id='verdict'"), 1)

    def test_passthrough_without_verdict(self):
        body = "<p>plain</p>"
        self.assertEqual(amod.enhance_result(body), body)

    def test_nonstring_yields_empty(self):
        self.assertEqual(amod.enhance_result(None), "")


class ScriptTest(unittest.TestCase):
    def test_scrolls_verdict_into_view(self):
        js = amod.verdict_js()
        self.assertIn("scrollIntoView", js)
        self.assertIn("getElementById('verdict')", js)

    def test_respects_reduced_motion(self):
        js = amod.verdict_js()
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("smooth", js)

    def test_no_scrollpos_overlap(self):
        emit = [amod.verdict_js(),
                amod.verdict_open(True),
                amod.verdict_block(True, "x"),
                amod.enhance_result("<p class='verdict ok'>x</p>"),
                amod.section_html()]
        for out in emit:
            self.assertNotIn("sessionStorage", out)
            self.assertNotIn("gw-scroll", out)
            self.assertNotIn("location.hash", out)


class StatusTest(unittest.TestCase):
    def test_section_html_anchor(self):
        body = amod.section_html()
        self.assertIn("id='status-b7-autoscroll'", body)
        self.assertIn("autoscroll.py", body)


if __name__ == "__main__":
    unittest.main()
