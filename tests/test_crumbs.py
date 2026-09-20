"""Page-level breadcrumb trail (I-3)."""
import unittest

from groundwork import crumbs as crumbsmod
from groundwork import filemap as fmmod


class TrailTest(unittest.TestCase):
    def test_empty_renders_nothing(self):
        self.assertEqual(crumbsmod.trail([]), "")
        self.assertEqual(crumbsmod.trail(None), "")

    def test_single_current_page(self):
        body = crumbsmod.trail([("Due", None)])
        self.assertIn("id='crumbs'", body)
        self.assertIn("aria-label='Breadcrumb'", body)
        self.assertIn("aria-current='page'", body)
        self.assertIn("Due", body)
        self.assertNotIn("<a ", body)

    def test_module_depth(self):
        body = crumbsmod.trail([("Modules", "/modules"), ("My mod", None)])
        self.assertIn("<a href='/modules'>Modules</a>", body)
        self.assertIn("aria-current='page'>My mod</span>", body)
        self.assertIn(" › ", body)

    def test_full_four_level_chain(self):
        body = crumbsmod.trail([
            ("Due", "/due"), ("My mod", "/modules/m1"),
            ("Add", "/modules/m1#lesson-add"), ("Card one", None)])
        self.assertEqual(body.count(" › "), 3)
        self.assertIn("href='/modules/m1#lesson-add'", body)
        self.assertIn("aria-current='page'>Card one</span>", body)

    def test_labels_are_escaped(self):
        body = crumbsmod.trail([("<b>Mod</b>", "/modules"), ("a&b", None)])
        self.assertIn("&lt;b&gt;Mod&lt;/b&gt;", body)
        self.assertIn("a&amp;b", body)
        self.assertNotIn("<b>Mod</b>", body)

    def test_unsafe_href_renders_as_text(self):
        for bad in ("https://evil.example/x", "//evil/x", "/a b",
                    "/a'b", "/a<b>", "", None):
            with self.subTest(href=bad):
                body = crumbsmod.trail([("Modules", bad), ("Here", None)])
                self.assertNotIn("<a href", body.split(" › ")[0])

    def test_blank_and_malformed_segments_skipped(self):
        body = crumbsmod.trail([("  ", "/modules"), ("Real", None),
                                "nonsense", ("", ""), (None, None)])
        self.assertIn("Real", body)
        self.assertNotIn("nonsense", body)

    def test_non_link_middle_segment(self):
        body = crumbsmod.trail([("Due", "/due"), ("Orphan", ""), ("Card", None)])
        self.assertIn("<span>Orphan</span>", body)

    def test_complements_filemap_without_duplicating(self):
        page = crumbsmod.trail([("Modules", "/modules"), ("M", None)])
        tree = fmmod.file_map(["a/b.py"], "a/b.py")
        self.assertIn("id='crumbs'", page)
        self.assertNotIn("minitree", page)
        self.assertIn("id='filemap'", tree)
        self.assertNotIn("id='crumbs'", tree)

    def test_section_html_anchor_and_demo(self):
        body = crumbsmod.section_html()
        self.assertIn("id='status-b6-crumbs'", body)
        self.assertIn("id='crumbs'", body)
        self.assertIn("/modules", body)


if __name__ == "__main__":
    unittest.main()
