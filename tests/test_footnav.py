"""Site footer sitemap (I-10)."""
import unittest

from groundwork import footnav as fnmod
from groundwork import sitemap as sitemapmod


class FootnavTest(unittest.TestCase):
    def test_four_groups_in_order(self):
        heads = [h for h, _ in fnmod.sections()]
        self.assertEqual(heads, ["Due", "Modules", "History", "About"])

    def test_every_href_matches_sitemap_routes(self):
        self.assertEqual(fnmod.check(), [])

    def test_all_sitemap_core_routes_reachable(self):
        hrefs = {h for _, links in fnmod.sections()
                 for _, h in links}
        for route in ("due", "modules", "reviews", "tour", "status"):
            self.assertIn("/" + route if route != "" else "/", hrefs)

    def test_footer_has_site_anchor(self):
        self.assertIn("id='site-footer'", fnmod.footer())

    def test_footer_has_sitemap_nav_label(self):
        self.assertIn("aria-label='Site map'", fnmod.footer())

    def test_footer_has_tagline(self):
        self.assertIn(fnmod.TAGLINE, fnmod.footer())

    def test_footer_has_status_link(self):
        self.assertIn("<a href='/status'>Status</a>", fnmod.footer())

    def test_active_link_marked(self):
        out = fnmod.footer(active="/due")
        self.assertIn("<a href='/due' aria-current='page'>", out)

    def test_labels_escaped(self):
        out = fnmod.section_html("A&B", (("<X>", "/due"),))
        self.assertIn("A&amp;B", out)
        self.assertIn("&lt;X&gt;", out)

    def test_status_anchor_prefix(self):
        self.assertIn("id='status-b6-footnav'",
                      fnmod.section_html_status())

    def test_pure_no_db(self):
        # No DB import: rendering never touches the database.
        self.assertNotIn("dbmod", dir(fnmod))


if __name__ == "__main__":
    unittest.main()
