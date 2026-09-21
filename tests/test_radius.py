"""Radius scale tokens (I-67)."""
import unittest

from groundwork import radius as radiusmod


class RadiusTest(unittest.TestCase):
    def test_root_block_with_all_tokens(self):
        css = radiusmod.radius_css()
        self.assertTrue(css.startswith(":root{"))
        self.assertIn("--r-card:12px;", css)
        self.assertIn("--r-control:8px;", css)
        self.assertIn("--r-chip:999px;", css)

    def test_legacy_mapping(self):
        self.assertEqual(radiusmod.token_for("10px"), "var(--r-card)")
        self.assertEqual(radiusmod.token_for("6px"), "var(--r-control)")
        self.assertEqual(radiusmod.token_for("999px"), "var(--r-chip)")

    def test_out_of_scale_and_bad_input_never_raise(self):
        for bad in ("4px", "2px", "0", "", None, 6, ["6px"]):
            self.assertEqual(radiusmod.token_for(bad), "")

    def test_section_anchor(self):
        self.assertIn("status-b11-radius", radiusmod.section_html())


if __name__ == "__main__":
    unittest.main()
