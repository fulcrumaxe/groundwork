"""Theme Modules like a library shelf (I-72)."""
import re
import unittest

from groundwork import cover as covermod
from groundwork import shelf as shelfmod


class ShelfTest(unittest.TestCase):
    def test_targets_real_module_card_selectors(self):
        css = shelfmod.shelf_css()
        for sel in (".modcard", ".modcard--clickable"):
            self.assertIn(sel, css)

    def test_spine_accent_bar_and_elevation(self):
        css = shelfmod.shelf_css().replace(" ", "")
        self.assertIn("border-left:", css)
        self.assertIn("--shelf-spine", css)
        self.assertIn("box-shadow:", css)

    def test_spine_agrees_with_cover_palette(self):
        for repo in ("groundwork", "myrepo", "a/b"):
            self.assertEqual(shelfmod.shelf_spine(repo),
                             covermod.cover_color(repo))
        self.assertRegex(shelfmod.shelf_spine("x"), r"^#[0-9a-f]{6}$")

    def test_reduced_motion_gate_disables_transition(self):
        css = shelfmod.shelf_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("transition:none", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = shelfmod.shelf_css().lower()
        self.assertNotIn("<style", css)

    def test_motion_budget_honored(self):
        css = shelfmod.shelf_css()
        durations = [int(m.group(1))
                     for m in re.finditer(r"(\d+)\s*ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLessEqual(ms, 300)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "", 0, 123, object(), ["x"], {"r": 1}):
            color = shelfmod.shelf_spine(bad)
            self.assertRegex(color, r"^#[0-9a-f]{6}$")
            decl = shelfmod.spine_decl(bad)
            self.assertIn("--shelf-spine:", decl)
        self.assertEqual(shelfmod.selectors(),
                         (".modcard", ".modcard--clickable"))
        # Deterministic: same input, same color.
        self.assertEqual(shelfmod.shelf_spine("abc"),
                         shelfmod.shelf_spine("abc"))

    def test_section_html_anchor(self):
        html = shelfmod.section_html()
        self.assertIn("id='status-b12-shelf'", html)

    def test_tour_entry_shape(self):
        entry = shelfmod.tour_entry()
        self.assertEqual(entry["id"], "library-shelf")
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["title"], "Library shelf")
        self.assertTrue(entry["blurb"])
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b12-shelf")
        self.assertEqual(entry["anchor"], shelfmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
