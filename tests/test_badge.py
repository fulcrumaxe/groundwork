"""README badge (F-386): live owned-count SVG for any README."""
import unittest
import xml.etree.ElementTree as ET

from groundwork import badge as badgemod

from test_web import handler_for, make_module


class BadgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("badge mod")

    def test_svg_is_valid_and_counts(self):
        out = badgemod.badge_svg(self.db)
        root = ET.fromstring(out)
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        owned, total = badgemod.counts(self.db)
        self.assertIn(f"{owned}/{total} concepts owned", out)

    def test_route_and_status_link(self):
        self.assertIn("<svg", handler_for(self.db).badge_svg())
        self.assertIn("status-badge", handler_for(self.db).status_html())


if __name__ == "__main__":
    unittest.main()
