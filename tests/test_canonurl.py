"""Language-prefix-free canonical URLs (I-33)."""
import unittest

from groundwork import canonurl as mod


class CanonicalTest(unittest.TestCase):
    def test_plain_paths_unchanged(self):
        for p in ("/", "/due", "/modules", "/reviews", "/debt",
                  "/diagnose", "/status", "/tour", "/journal",
                  "/styleguide", "/api/due.json", "/export/anki.tsv",
                  "/badge.svg", "/sitemap.xml"):
            with self.subTest(path=p):
                self.assertEqual(mod.canonical(p), p)

    def test_language_prefix_stripped(self):
        self.assertEqual(mod.canonical("/en/due"), "/due")
        self.assertEqual(mod.canonical("/EN/modules"), "/modules")
        self.assertEqual(mod.canonical("/pt-BR/journal"), "/journal")
        self.assertEqual(mod.canonical("/en"), "/")
        self.assertEqual(mod.canonical("/en/"), "/")
        self.assertEqual(mod.canonical("/fr/api/due.json?x=1"), "/api/due.json?x=1")

    def test_debt_never_stripped(self):
        self.assertEqual(mod.canonical("/debt"), "/debt")
        self.assertEqual(mod.canonical("/debt/"), "/debt")

    def test_trailing_slash_rule(self):
        self.assertEqual(mod.canonical("/due/"), "/due")
        self.assertEqual(mod.canonical("/modules/"), "/modules")
        self.assertEqual(mod.canonical("/"), "/")
        self.assertEqual(mod.canonical("/due//"), "/due")

    def test_protocol_relative_falls_home(self):
        # Leading // is an open-redirect shape: fail closed, like
        # originguard and web._safe_origin.
        self.assertEqual(mod.canonical("//due//"), "/")
        self.assertEqual(mod.canonical("//evil/x"), "/")

    def test_query_and_fragment_preserved_verbatim(self):
        self.assertEqual(mod.canonical("/due?mode=one"), "/due?mode=one")
        self.assertEqual(mod.canonical("/en/due?mode=one"), "/due?mode=one")
        self.assertEqual(mod.canonical("/modules?sort=oldest&repo=a/b"), "/modules?sort=oldest&repo=a/b")
        self.assertEqual(mod.canonical("/modules/m1#lesson-add"), "/modules/m1#lesson-add")

    def test_hostile_input_falls_home(self):
        for bad in ("https://evil.example/x", "//evil/x", "/a b",
                    "/a'b", '/a"b', "/a<b>", "/a\\b", "", "   ", None, 42, ["../due"]):
            with self.subTest(raw=bad):
                self.assertEqual(mod.canonical(bad), "/")

    def test_unknown_paths_normalize_but_are_not_contract(self):
        self.assertEqual(mod.canonical("/en/nope/"), "/nope")
        paths = {p for p, _ in mod.url_contract()}
        self.assertNotIn("/nope", paths)

    def test_is_canonical(self):
        self.assertTrue(mod.is_canonical("/due"))
        self.assertFalse(mod.is_canonical("/en/due"))
        self.assertFalse(mod.is_canonical("/due/"))
        self.assertFalse(mod.is_canonical(None))


class ContractTest(unittest.TestCase):
    def test_covers_every_web_route(self):
        paths = {p for p, _ in mod.url_contract()}
        for p in ("/", "/due", "/modules", "/reviews", "/debt",
                  "/diagnose", "/status", "/tour", "/journal",
                  "/styleguide", "/search", "/api/modules.json",
                  "/api/due.json", "/export/anki.tsv",
                  "/export/reviews.csv", "/export/me.json",
                  "/badge.svg", "/feed.xml", "/sitemap.xml",
                  "/robots.txt", "/mcp"):
            with self.subTest(path=p):
                self.assertIn(p, paths)

    def test_no_healthz_absent_route(self):
        paths = {p for p, _ in mod.url_contract()}
        self.assertNotIn("/healthz", paths)

    def test_rows_are_path_purpose_pairs(self):
        for row in mod.url_contract():
            path, purpose = row
            self.assertTrue(path.startswith("/"))
            self.assertTrue(purpose.strip())


class SectionTest(unittest.TestCase):
    def test_anchor_and_table(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-canonurl'", body)
        self.assertIn("/due", body)
        self.assertIn("<table>", body)

    def test_no_db_path_arg(self):
        import inspect
        self.assertEqual(list(inspect.signature(mod.section_html).parameters), [])


if __name__ == "__main__":
    unittest.main()
