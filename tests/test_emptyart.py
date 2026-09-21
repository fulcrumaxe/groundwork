"""Empty-state illustrations (I-69)."""
import unittest

from groundwork import empty as emptymod
from groundwork import emptyart as artmod


class EmptyArtTest(unittest.TestCase):
    def test_known_pages_return_svg_currentcolor(self):
        for page in ("due", "modules", "history", "journal", "diagnose"):
            svg = artmod.art_for(page)
            self.assertIn("<svg", svg)
            self.assertIn("stroke='currentColor'", svg)
            self.assertIn("<title>", svg)

    def test_no_emoji_no_motion(self):
        for page in ("due", "modules", "history", "journal",
                     "diagnose", "nope"):
            svg = artmod.art_for(page)
            self.assertNotIn("<animate", svg)
            self.assertNotIn("animation", svg)
            for ch in svg:
                self.assertLess(ord(ch), 0x2500,
                                f"non-line-art char in {page}")

    def test_unknown_page_falls_back(self):
        svg = artmod.art_for("nope")
        self.assertIn("<svg", svg)
        self.assertIn("Nothing here yet", svg)

    def test_art_never_raises(self):
        for bad in (None, 5, ["due"]):
            self.assertIn("<svg", artmod.art_for(bad))

    def test_with_art_delegates_copy(self):
        for page in ("due", "modules", "history", "journal"):
            body = artmod.with_art(page)
            self.assertIn("<svg", body)
            self.assertIn(emptymod.empty_state(page), body)
            self.assertIn("id='empty'", body)
            self.assertIn("<a href=", body)

    def test_section_anchor(self):
        self.assertIn("status-b11-emptyart", artmod.section_html())


if __name__ == "__main__":
    unittest.main()
