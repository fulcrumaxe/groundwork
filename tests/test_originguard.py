"""Origin allowlist guard (I-34)."""
import unittest

from groundwork import originguard as mod


class SafeOriginAttackTest(unittest.TestCase):
    def test_protocol_relative_rejected(self):
        self.assertEqual(mod.safe_origin("//evil/x"), "/")

    def test_scheme_rejected(self):
        for bad in ("javascript:alert(1)", "https://evil/", "data:text/html,x"):
            self.assertEqual(mod.safe_origin(bad), "/", bad)

    def test_encoded_slash_rejected(self):
        for bad in ("/%2f Evil", "/%2Fevil", "/due%2f..", "/%5cevil", "/%00x"):
            self.assertEqual(mod.safe_origin(bad), "/", bad)

    def test_backslash_rejected(self):
        for bad in ("\\evil", "/\\evil", "/due\\x", "\\\\server"):
            self.assertEqual(mod.safe_origin(bad), "/", bad)

    def test_absolute_url_rejected(self):
        self.assertEqual(mod.safe_origin("https://evil.example/phish"), "/")
        self.assertEqual(mod.safe_origin("http:/x"), "/")

    def test_empty_none_fall_back(self):
        self.assertEqual(mod.safe_origin(""), "/")
        self.assertEqual(mod.safe_origin(None), "/")
        self.assertEqual(mod.safe_origin("   "), "/")
        self.assertEqual(mod.safe_origin(12345), "/")

    def test_unknown_route_rejected(self):
        self.assertEqual(mod.safe_origin("/no-such-page"), "/")
        self.assertEqual(mod.safe_origin("/api/due.json"), "/")
        self.assertEqual(mod.safe_origin("/export/anki.tsv"), "/")

    def test_custom_default_used(self):
        self.assertEqual(mod.safe_origin("//evil", default="/due"), "/due")


class SafeOriginValidTest(unittest.TestCase):
    def test_exact_pages_kept(self):
        for good in ("/", "/due", "/reviews", "/modules", "/status",
                     "/tour", "/journal", "/search", "/debt", "/diagnose",
                     "/styleguide"):
            self.assertEqual(mod.safe_origin(good), good, good)

    def test_module_detail_kept(self):
        self.assertEqual(mod.safe_origin("/modules/abc123"), "/modules/abc123")

    def test_query_string_kept(self):
        self.assertEqual(mod.safe_origin("/due?mode=one"), "/due?mode=one")
        self.assertEqual(mod.safe_origin("/modules?repo=x"), "/modules?repo=x")
        self.assertEqual(mod.safe_origin("/search?q=fsrs"), "/search?q=fsrs")

    def test_trailing_slash_normalized(self):
        self.assertEqual(mod.safe_origin("/due/"), "/due")
        self.assertEqual(mod.safe_origin("/modules/abc/"), "/modules/abc")

    def test_fragment_dropped(self):
        self.assertEqual(mod.safe_origin("/due#card-c9"), "/due")

    def test_bad_default_falls_to_root(self):
        self.assertEqual(mod.safe_origin("//evil", default="//evil"), "/")


class CollectorsTest(unittest.TestCase):
    def test_known_routes_cover_nav_pages(self):
        routes = mod.known_routes()
        for page in ("/", "/due", "/reviews", "/modules", "/status"):
            self.assertIn(page, routes)

    def test_producers_name_origin_emitters(self):
        names = [s for _, s in mod.origin_producers()]
        for sym in ("answer_widget", "block_html", "button_html",
                    "dispute_form_html"):
            self.assertIn(sym, names)

    def test_consumers_cover_review_handlers(self):
        sites = " ".join(h for _, h, _ in mod.origin_consumers())
        self.assertIn("/cards/<id>/review", sites)
        self.assertIn("/concepts/<id>/rate", sites)

    def test_audit_explains_verdict(self):
        ok = mod.audit_origin("/due")
        self.assertEqual(ok, {"input": "/due", "output": "/due",
                             "allowed": True, "reason": "ok"})
        bad = mod.audit_origin("//evil")
        self.assertFalse(bad["allowed"])
        self.assertEqual(bad["output"], "/")


class RenderTest(unittest.TestCase):
    def test_section_html_anchor(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-originguard'", body)
        self.assertIn("originguard.py", body)

    def test_tour_entry_shape(self):
        entry = mod.tour_entry()
        self.assertEqual(entry["id"], "originguard-allowlist")
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b8-originguard")


if __name__ == "__main__":
    unittest.main()
