"""Merged header + footer nav (I-39)."""
import unittest

from groundwork import sitenav as mod
from groundwork import web as webmod


class SitenavTest(unittest.TestCase):
    def test_table_shape(self):
        self.assertEqual(len(mod.items()), 6)
        for row in mod.items():
            self.assertEqual(len(row), 3)
            key, href, label = row
            self.assertTrue(key and href.startswith("/") and label)

    def test_table_matches_web_nav(self):
        # One source of truth: the module table is web.NAV's content.
        self.assertEqual(list(webmod.NAV), list(mod.items()))
        self.assertEqual(
            list(mod.items()),
            [("projects", "/", "Projects"),
             ("due", "/due", "Due"),
             ("modules", "/modules", "Modules"),
             ("history", "/reviews", "History"),
             ("debt", "/debt", "Debt"),
             ("tour", "/tour", "Tour")])

    def test_href_of(self):
        self.assertEqual(mod.href_of("history"), "/reviews")
        self.assertEqual(mod.href_of("nope"), "")
        self.assertEqual(mod.href_of("nope", "/due"), "/due")

    def test_header_active_marked(self):
        # Double quotes: byte-identical with the web.page() header.
        out = mod.header_nav("due")
        self.assertIn("<a href='/due' aria-current=\"page\">Due</a>", out)
        self.assertNotIn("href='/' aria-current", out)

    def test_header_matches_page_chrome(self):
        # The helper must render exactly what web.page() emits today.
        raw = webmod.page("T", "<p>x</p>", active="due",
                          page_id="due").decode()
        for link in mod.header_nav("due").split(" · "):
            self.assertIn(link, raw)

    def test_footer_active_marked(self):
        out = mod.footer_nav("due")
        self.assertIn("<a href='/due' aria-current='page'>Due</a>", out)
        self.assertIn("id='site-footer'", out)

    def test_counts_render_in_header(self):
        out = mod.header_nav("due", {"due": 3})
        self.assertIn("Due (3)", out)

    def test_counts_absent_without_dict(self):
        self.assertNotIn("(", mod.header_nav("due"))

    def test_unknown_active_marks_nothing(self):
        for out in (mod.header_nav("nope"), mod.footer_nav("nope")):
            self.assertNotIn("aria-current", out)

    def test_hostile_labels_keys_escaped(self):
        out = mod._header_link("x", "/due", "<X>&", "x")
        self.assertIn("&lt;X&gt;&amp;", out)
        out = mod.header_nav("due", {"due": "<3>"})
        self.assertIn("(&lt;3&gt;)", out)

    def test_status_anchor_prefix(self):
        self.assertIn("id='status-b8-sitenav'", mod.section_html())

    def test_pure_no_db(self):
        self.assertNotIn("dbmod", dir(mod))


if __name__ == "__main__":
    unittest.main()
