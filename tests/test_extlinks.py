"""External vs internal link distinction (I-31)."""
import unittest

from groundwork import extlinks as mod


class ClassifyTest(unittest.TestCase):
    def test_external_urls(self):
        for href in ("https://example.com/x", "http://a.b/",
                     "//cdn.example.com/x.js"):
            self.assertEqual(mod.classify(href), "external")

    def test_external_case_insensitive(self):
        self.assertEqual(mod.classify("HTTPS://example.com/"), "external")

    def test_internal_routes_and_relative_hrefs(self):
        for href in ("/status", "/modules/abc?level=2",
                     "/due#lesson-add", "lessons/intro", "a/b/c"):
            self.assertEqual(mod.classify(href), "internal")

    def test_repo_paths(self):
        for href in ("groundwork/extlinks.py", "tests/test_extlinks.py",
                     "static/app.css", "./calc.py", "../x.py",
                     "groundwork/extlinks.py#L12"):
            self.assertEqual(mod.classify(href), "repo")

    def test_skip_kinds(self):
        for href in ("#lesson-add", "mailto:a@b.c", "tel:+123",
                     "data:text/plain,x", "javascript:void(0)",
                     "", "   ", None, 42):
            self.assertEqual(mod.classify(href), "skip")


class IsExternalTest(unittest.TestCase):
    def test_truth_table(self):
        self.assertTrue(mod.is_external("https://example.com/"))
        self.assertTrue(mod.is_external("//cdn/x.js"))
        self.assertFalse(mod.is_external("/status"))
        self.assertFalse(mod.is_external("groundwork/extlinks.py"))
        self.assertFalse(mod.is_external("#frag"))
        self.assertFalse(mod.is_external("mailto:a@b.c"))
        self.assertFalse(mod.is_external(None))


class DecorateTest(unittest.TestCase):
    def test_external_gains_class_rel_marker(self):
        out = mod.decorate("<a href='https://example.com/x'>Docs</a>")
        self.assertIn("ext-link", out)
        self.assertIn("rel=\"noopener\"", out)
        self.assertIn("ext-marker", out)
        self.assertIn("(external link)", out)

    def test_protocol_relative_decorated(self):
        out = mod.decorate("<a href='//cdn/x.js'>CDN</a>")
        self.assertIn("ext-link", out)

    def test_internal_repo_anchor_mailto_untouched(self):
        for raw in ("<a href='/status'>S</a>",
                    "<a href='groundwork/extlinks.py'>R</a>",
                    "<a href='#frag'>F</a>",
                    "<a href='mailto:a@b.c'>M</a>",
                    "<a href='lessons/intro'>L</a>"):
            self.assertEqual(mod.decorate(raw), raw)

    def test_preserves_existing_class_and_rel(self):
        out = mod.decorate(
            "<a class='nav' rel='noreferrer' "
            "href=\"https://example.com/\">E</a>")
        self.assertIn("nav", out)
        self.assertIn("ext-link", out)
        self.assertIn("noreferrer", out)
        self.assertIn("noopener", out)

    def test_never_doubles(self):
        once = mod.decorate("<a href='https://example.com/'>E</a>")
        self.assertEqual(mod.decorate(once), once)

    def test_hostile_and_unquoted_hrefs_untouched(self):
        for raw in ('<a href=https://example.com/>U</a>',
                    '<a href="https://x industrial">Q</a>'.replace(
                        " industrial", '"onmouseover="alert(1)'),
                    "<a>No href</a>",
                    "plain text"):
            out = mod.decorate(raw)
            self.assertNotIn("ext-marker", out)

    def test_non_string_passthrough(self):
        self.assertIsNone(mod.decorate(None))
        self.assertEqual(mod.decorate(123), 123)


class SectionTest(unittest.TestCase):
    def test_status_anchor(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-extlinks'", body)
        self.assertIn("ext-link", body)


if __name__ == "__main__":
    unittest.main()
