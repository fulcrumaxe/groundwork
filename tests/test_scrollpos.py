"""Scroll-position preservation (I-14)."""
import unittest

from groundwork import scrollpos as spmod


class OriginTest(unittest.TestCase):
    def test_bare_path_kept(self):
        self.assertEqual(spmod.origin_with_anchor("/due", "c1"), "/due#card-c1")

    def test_existing_anchor_wins(self):
        self.assertEqual(spmod.origin_with_anchor("/due#card-x", "c1"), "/due#card-x")

    def test_unsafe_origin_falls_back(self):
        self.assertTrue(spmod.origin_with_anchor("https://evil/x", "c1").startswith("/"))

    def test_split_origin(self):
        self.assertEqual(spmod.split_origin("/due#card-c9"),
                         {"path": "/due", "anchor": "card-c9"})

    def test_split_bad_anchor_dropped(self):
        parts = spmod.split_origin("/due#<script>")
        self.assertEqual(parts["path"], "/due")
        self.assertNotIn("<", parts["anchor"])

    def test_card_anchor_sanitised(self):
        self.assertEqual(spmod.card_anchor("a/b c!"), "card-abc")

    def test_back_href_matches_origin(self):
        self.assertEqual(spmod.back_href("/due", "c2"), "/due#card-c2")


class RenderTest(unittest.TestCase):
    def test_origin_field_escaped(self):
        out = spmod.origin_field("/due", 'c"1')
        self.assertIn("name='origin'", out)
        self.assertIn("/due#card-c1", out)
        self.assertNotIn('"1', out.split("value='", 1)[1].split("'", 1)[0].replace("#card-c1", ""))

    def test_record_js_saves_scrolly(self):
        js = spmod.record_js()
        self.assertIn("sessionStorage.setItem", js)
        self.assertIn("scrollY", js)

    def test_restore_js_reads_key_and_hash(self):
        js = spmod.restore_js("/due")
        self.assertIn("sessionStorage.getItem", js)
        self.assertIn("location.hash", js)
        self.assertIn("gw-scroll:/due", js)

    def test_result_back_link_anchored(self):
        link = spmod.result_back_link("/due", "c7")
        self.assertIn("href='/due#card-c7'", link)
        self.assertIn("Continue where you left off", link)

    def test_section_html_anchor(self):
        body = spmod.section_html()
        self.assertIn("id='status-b6-scrollpos'", body)
        self.assertIn("scrollpos.py", body)


if __name__ == "__main__":
    unittest.main()
