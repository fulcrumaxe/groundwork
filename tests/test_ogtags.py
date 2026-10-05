"""Open Graph tags (I-88): shared links unfurl with title + lede."""
import unittest

from groundwork import ogtags as ogmod


class OgtagsTest(unittest.TestCase):
    def test_minimal_set_present(self):
        tags = ogmod.og_tags("Module", "Study closures.")
        self.assertIn("og:title", tags)
        self.assertIn("og:type", tags)
        self.assertIn("og:site_name", tags)
        self.assertIn("og:description", tags)
        self.assertIn("content='Module'", tags)
        self.assertIn("Study closures.", tags)

    def test_no_localhost_url_lie(self):
        tags = ogmod.og_tags("Module", "lede")
        self.assertNotIn("og:url", tags)
        self.assertNotIn("127.0.0.1", tags)
        self.assertNotIn("localhost", tags)

    def test_escaping_and_caps(self):
        import html as htmlmod
        tags = ogmod.og_tags("<script>'x'</script>", "a\nb  <c>" * 100)
        self.assertNotIn("<script>", tags)
        self.assertNotIn("<c>", tags)
        raw = tags.split("content='")[-1].rsplit("'>", 1)[0]
        # Cap applies to the real text; escaping may inflate the wire.
        self.assertLessEqual(len(htmlmod.unescape(raw)), 300)
        self.assertTrue(raw.endswith("..."))

    def test_defaults_when_blank(self):
        tags = ogmod.og_tags("", "")
        self.assertIn("Groundwork", tags)
        self.assertIn("learning companion", tags)
        for bad in (None, 42, object()):
            self.assertIn("og:title", ogmod.og_tags(bad, bad))

    def test_section_html_anchor(self):
        html = ogmod.section_html()
        self.assertIn("id='status-b13-ogtags'", html)
        self.assertIn("og_tags", html)

    def test_tour_entry_shape(self):
        e = ogmod.tour_entry()
        self.assertEqual(e, {
            "id": "share-unfurls",
            "kind": "improvement",
            "title": "Share unfurls",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-ogtags",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "ogtags.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


class ModuleLedeRouteTest(unittest.TestCase):
    """The /modules/<id> route passes the summary as the unfurl lede.

    Regression (demo-video batch 13): the module promised that module
    pages pass their lede through so shares name the concept studied,
    but the route never passed one — every module shared as generic
    "Module" + the default description.
    """

    def _get(self, db, path):
        import io

        from groundwork import web as webmod
        h = webmod.Handler.__new__(webmod.Handler)
        h.db_path = db
        h.path = path
        h.headers = {}
        h.rfile = io.BytesIO(b"")
        captured = {}
        h._send = lambda data, code=200, ctype="text/html": captured.update(
            data=data, code=code, ctype=ctype)
        h.do_GET()
        return captured

    def test_module_share_names_the_summary(self):
        from test_web import make_module
        _tmp, db, _server, out = make_module("ogtags lede module")
        got = self._get(db, f"/modules/{out['module_id']}")
        self.assertEqual(got["code"], 200)
        raw = got["data"].decode()
        self.assertIn("ogtags lede module", raw)
        desc = [line for line in raw.split("><")
                if "og:description" in line]
        self.assertTrue(desc, "no og:description on module page")
        self.assertIn("ogtags lede module", desc[0])

    def test_unknown_module_stays_404_without_lede(self):
        from test_web import make_module
        _tmp, db, _server, _out = make_module("ogtags lede missing")
        got = self._get(db, "/modules/does-not-exist")
        self.assertEqual(got["code"], 404)

    def test_module_lede_never_raises(self):
        self.assertEqual(ogmod.module_lede(None, None), "")
        self.assertEqual(ogmod.module_lede("/no/such.db", "x"), "")
        self.assertEqual(ogmod.module_lede("", ""), "")


if __name__ == "__main__":
    unittest.main()
