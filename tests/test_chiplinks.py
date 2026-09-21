"""Concept-chip lesson links (I-22)."""
import unittest

from groundwork import chiplinks as chipmod
from groundwork import lessons as lesmod


class ChipLinksTest(unittest.TestCase):
    def test_slug_matches_lessons_scheme(self):
        for text in ("Add", "read_csv", "Hello, World!",
                     "  spaced  out  ", "MixedCASE 123", "a/b:c d"):
            self.assertEqual(chipmod.slug(text), lesmod.slug(text))

    def test_slug_edge_cases(self):
        self.assertEqual(chipmod.slug(""), "lesson")
        self.assertEqual(chipmod.slug("   "), "lesson")
        self.assertEqual(chipmod.slug("---"), "lesson")
        self.assertEqual(chipmod.slug("Add"), "add")
        self.assertNotIn(" ", chipmod.slug("a b"))
        self.assertNotIn("/", chipmod.slug("a/b"))

    def test_lesson_anchor_prefixes_slug(self):
        self.assertEqual(chipmod.lesson_anchor("Add"), "lesson-add")
        self.assertTrue(chipmod.lesson_anchor("x").startswith("lesson-"))

    def test_href_shape(self):
        self.assertEqual(chipmod.chip_href("m1", "Add"), "/modules/m1#lesson-add")

    def test_href_blank_concept_falls_back_to_module(self):
        self.assertEqual(chipmod.chip_href("m1", ""), "/modules/m1")
        self.assertEqual(chipmod.chip_href("m1", None), "/modules/m1")

    def test_href_blank_module_renders_empty(self):
        self.assertEqual(chipmod.chip_href("", "Add"), "")
        self.assertEqual(chipmod.chip_href(None, "Add"), "")

    def test_href_escapes_module_id(self):
        body = chipmod.chip_href("m'1", "Add")
        self.assertNotIn("m'1", body)

    def test_chip_link_wraps_status_label(self):
        body = chipmod.chip_link("m1", "Add", "Owned")
        self.assertIn("href='/modules/m1#lesson-add'", body)
        # Batch 10 I-58: Owned chips carry the reveal class.
        self.assertIn("<span class='chip owned-badge'>Owned</span>", body)

    def test_non_owned_status_stays_plain_chip(self):
        for label in ("New", "Stale", "Learning"):
            body = chipmod.chip_link("m1", "Add", label)
            self.assertIn(f"<span class='chip'>{label}</span>", body)

    def test_chip_link_escapes_label(self):
        body = chipmod.chip_link("m1", "Add", "<b>x</b>")
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_chip_link_without_module_is_plain_chip(self):
        body = chipmod.chip_link("", "Add", "Owned")
        self.assertNotIn("<a ", body)
        # Batch 10 I-58: Owned chips carry the reveal class.
        self.assertIn("<span class='chip owned-badge'>Owned</span>", body)

    def test_never_raises(self):
        for mid in (None, 123, ["m1"], {"id": "m1"}):
            for concept in (None, 123, ["Add"], {"n": "Add"}):
                for label in (None, 123, "<i>x</i>"):
                    chipmod.slug(concept)
                    chipmod.lesson_anchor(concept)
                    chipmod.chip_href(mid, concept)
                    chipmod.chip_link(mid, concept, label)
        chipmod.section_html()
        chipmod.section_html("/tmp/x.db")

    def test_status_section_has_stable_anchor(self):
        body = chipmod.section_html()
        self.assertIn("id='status-b7-chiplinks'", body)


if __name__ == "__main__":
    unittest.main()
