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
        tags = ogmod.og_tags("<script>'x'</script>", "a\nb  <c>" * 100)
        self.assertNotIn("<script>", tags)
        self.assertNotIn("<c>", tags)
        desc = tags.split("og:description", 1)[1]
        self.assertLess(len(desc), 500)

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


if __name__ == "__main__":
    unittest.main()
