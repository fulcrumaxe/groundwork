"""Due-count favicon (I-87): tab icon carries page state."""
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from groundwork import pageicon as pimod


def _svg_of(uri):
    assert uri.startswith("data:image/svg+xml,")
    return ET.fromstring(unquote(uri.split(",", 1)[1]))


class PageiconTest(unittest.TestCase):
    def test_zero_due_is_plain_mark(self):
        self.assertEqual(pimod.badge_text(0), "")
        self.assertEqual(pimod.badge_text(-3), "")
        self.assertEqual(pimod.badge_text("many"), "")
        self.assertEqual(pimod.badge_text(None), "")
        root = _svg_of(pimod.icon_data_uri(0))
        texts = [e.text for e in root.iter(
            "{http://www.w3.org/2000/svg}text")]
        self.assertEqual(texts, ["G"])

    def test_badge_counts_and_caps(self):
        self.assertEqual(pimod.badge_text(7), "7")
        self.assertEqual(pimod.badge_text(150), "99+")
        root = _svg_of(pimod.icon_data_uri(12))
        texts = [e.text for e in root.iter(
            "{http://www.w3.org/2000/svg}text")]
        self.assertIn("12", texts)
        root = _svg_of(pimod.icon_data_uri(150))
        texts = [e.text for e in root.iter(
            "{http://www.w3.org/2000/svg}text")]
        self.assertIn("99+", texts)

    def test_data_uri_is_link_safe(self):
        uri = pimod.icon_data_uri(5)
        self.assertNotIn("#", uri)
        self.assertNotIn("<", uri)
        self.assertNotIn(" ", uri)
        _svg_of(uri)  # round-trips to valid SVG

    def test_link_tag_over_counts(self):
        tag = pimod.link_tag({"due": 4})
        self.assertIn("rel='icon'", tag)
        self.assertIn("data:image/svg+xml,", tag)
        _svg_of(tag.split('href="', 1)[1].rstrip('">'))
        plain = pimod.link_tag(None)
        self.assertIn("rel='icon'", plain)
        root = _svg_of(plain.split('href="', 1)[1].rstrip('">'))
        texts = [e.text for e in root.iter(
            "{http://www.w3.org/2000/svg}text")]
        self.assertEqual(texts, ["G"])
        # Garbage counts never raise, never badge.
        self.assertIn("rel='icon'", pimod.link_tag({"due": object()}))

    def test_section_html_anchor(self):
        html = pimod.section_html()
        self.assertIn("id='status-b13-pageicon'", html)
        self.assertIn("icon_data_uri", html)

    def test_tour_entry_shape(self):
        e = pimod.tour_entry()
        self.assertEqual(e, {
            "id": "due-favicon",
            "kind": "improvement",
            "title": "Due-count favicon",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-pageicon",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "pageicon.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
