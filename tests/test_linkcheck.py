"""Quarterly link audit: extraction + verification + report (I-50)."""
import inspect
import unittest

from groundwork import canonurl
from groundwork import linkcheck as mod

SAMPLE_ROUTES = (
    ("/", "Projects landing"),
    ("/due", "Spaced review queue"),
    ("/modules", "Module library"),
    ("/modules/{mid}", "Module detail page"),
    ("/modules/{mid}/reset", "Module reset confirm + action"),
    ("/status", "Machine-room status page"),
)


class ExtractTest(unittest.TestCase):
    def test_collects_internal_links_in_order(self):
        html = ("<nav><a href='/due'>Due</a> · "
                "<a href=\"/modules\">Modules</a></nav>")
        self.assertEqual(mod.extract_links(html), ["/due", "/modules"])

    def test_skips_external_mailto_and_anchors(self):
        html = ("<a href='https://example.com/x'>E</a>"
                "<a href='//cdn.example/y'>C</a>"
                "<a href='mailto:a@b.c'>M</a>"
                "<a href='tel:+1'>T</a>"
                "<a href='#top'>A</a>"
                "<a href='/due'>D</a>")
        self.assertEqual(mod.extract_links(html), ["/due"])

    def test_malformed_html_never_raises(self):
        # An unterminated tag ("<a HREF='/due'") yields nothing: HTMLParser
        # buffers incomplete tags until close; tolerance means [] not raise.
        for bad, want in (("<a href='/due'>", ["/due"]),
                          ("<a href=/due>", ["/due"]),
                          ("<div><a href='/due'><span>oops", ["/due"]),
                          ("", []), (None, []), (42, []), (["<a>"], [])):
            with self.subTest(raw=bad):
                self.assertEqual(mod.extract_links(bad), want)
        self.assertEqual(mod.extract_links("<a HREF='/due'"), [])

    def test_non_anchor_hrefs_ignored(self):
        self.assertEqual(mod.extract_links("<link href='/due'>"), [])


class AuditTest(unittest.TestCase):
    def test_broken_internal_link_flagged(self):
        result = mod.audit_links(["/due", "/nope"], SAMPLE_ROUTES)
        self.assertEqual(result["ok"], ["/due"])
        self.assertEqual(result["broken"], ["/nope"])
        self.assertEqual(result["external_skipped"], 0)

    def test_external_counted_not_flagged(self):
        result = mod.audit_links(
            ["https://example.com/x", "//cdn.example/y", "/due"], SAMPLE_ROUTES)
        self.assertEqual(result["ok"], ["/due"])
        self.assertEqual(result["broken"], [])
        self.assertEqual(result["external_skipped"], 2)

    def test_query_fragment_lang_and_slash_stripped(self):
        links = ["/due?mode=one#top", "/en/modules", "/modules/",
                 "/modules/abc#lesson-add", "/pt-BR/due?x=1"]
        result = mod.audit_links(links, SAMPLE_ROUTES)
        self.assertEqual(result["broken"], [])
        self.assertEqual(result["ok"],
                         ["/due", "/modules", "/modules/abc"])

    def test_parameterized_routes_match_one_segment(self):
        result = mod.audit_links(
            ["/modules/abc", "/modules/abc/reset", "/modules/abc/extra"],
            SAMPLE_ROUTES)
        self.assertIn("/modules/abc", result["ok"])
        self.assertIn("/modules/abc/reset", result["ok"])
        self.assertEqual(result["broken"], ["/modules/abc/extra"])

    def test_consumes_canonical_route_table(self):
        html = "<a href='/due'>D</a><a href='/nope'>N</a>"
        result = mod.audit_links(mod.extract_links(html), canonurl.ROUTES)
        self.assertIn("/due", result["ok"])
        self.assertIn("/nope", result["broken"])

    def test_dedupes_first_seen_order_and_tolerates_junk(self):
        result = mod.audit_links(
            ["/due", "/due", None, 42, "#top", "/nope", "/nope"],
            SAMPLE_ROUTES)
        self.assertEqual(result["ok"], ["/due"])
        self.assertEqual(result["broken"], ["/nope"])

    def test_bad_input_audits_empty(self):
        self.assertEqual(mod.audit_links(None, SAMPLE_ROUTES),
                         {"ok": [], "broken": [], "external_skipped": 0})
        self.assertEqual(mod.audit_links(["/due"], None)["broken"], ["/due"])

    def test_langs_mirror_matches_canonurl(self):
        # LANGS is an attributed mirror of canonurl.LANGS; drift loudly.
        self.assertEqual(mod.LANGS, canonurl.LANGS)


class ReportTest(unittest.TestCase):
    def test_one_line_summary(self):
        line = mod.audit_report(
            {"ok": ["/due"], "broken": ["/nope"], "external_skipped": 1})
        self.assertNotIn("\n", line)
        self.assertEqual(
            line, "Link audit: 1 ok, 1 broken (/nope), 1 external skipped.")

    def test_clean_audit_line(self):
        self.assertEqual(
            mod.audit_report({"ok": ["/a"], "broken": [], "external_skipped": 0}),
            "Link audit: 1 ok, 0 broken, 0 external skipped.")

    def test_malformed_result_never_raises(self):
        for bad in (None, {}, {"ok": None}, "junk"):
            with self.subTest(raw=bad):
                line = mod.audit_report(bad)
                self.assertTrue(line.startswith("Link audit:"))
                self.assertNotIn("\n", line)


class SectionTest(unittest.TestCase):
    def test_anchor_and_module_mention(self):
        body = mod.section_html()
        self.assertIn("id='status-b9-linkcheck'", body)
        self.assertIn("groundwork/linkcheck.py", body)

    def test_no_db_path_arg(self):
        self.assertEqual(list(inspect.signature(mod.section_html).parameters), [])


if __name__ == "__main__":
    unittest.main()
