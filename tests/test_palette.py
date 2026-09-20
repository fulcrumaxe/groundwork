"""Palette CSS variables (I-51)."""
import unittest

from groundwork import palette as palettemod


class PaletteTest(unittest.TestCase):
    def test_root_block_with_all_tokens(self):
        css = palettemod.palette_css()
        self.assertTrue(css.startswith(":root{"))
        for token in ("--ink", "--paper", "--accent-due", "--accent-modules",
                      "--accent-history", "--pass", "--fail", "--stale"):
            self.assertIn(token, css)


if __name__ == "__main__":
    unittest.main()
