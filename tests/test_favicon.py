"""Site favicon: /favicon.ico serves a static SVG (no more console 404)."""
import unittest
import xml.etree.ElementTree as ET

from groundwork import favicon as faviconmod

from test_web import handler_for, make_module


class FaviconTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("favicon mod")

    def test_svg_is_valid(self):
        root = ET.fromstring(faviconmod.favicon_svg())
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_handler_delegates(self):
        self.assertIn("<svg", handler_for(self.db).favicon_svg())


if __name__ == "__main__":
    unittest.main()
