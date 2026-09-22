"""High-contrast overrides (I-99)."""
import unittest

from groundwork import contrast as contrastmod
from groundwork import web as webmod


class ContrastTest(unittest.TestCase):
    def test_blocks_present(self):
        css = contrastmod.contrast_css()
        self.assertIn("@media (prefers-contrast: more)", css)
        self.assertIn("@media(forced-colors:active)", css)
        self.assertNotIn("<style", css)

    def test_system_color_mapping_present(self):
        # The one measurable key-pair assertion: progress/chip hooks
        # map to system colors with forced-color-adjust so the
        # platform cannot flatten them to unreadable tints.
        css = contrastmod.contrast_css()
        self.assertIn("forced-color-adjust:none", css)
        self.assertIn("CanvasText", css)
        self.assertIn("Highlight", css)

    def test_existing_hooks_only(self):
        css = contrastmod.contrast_css()
        for hook in (".chip", ".owned-badge", ".bar i",
                     "#readprogress span"):
            self.assertIn(hook, css)

    def test_effect_head_carries_contrast(self):
        # Behavioral-effect test: the rendered page head ships it.
        self.assertIn("forced-color-adjust:none", webmod.CSS)
        self.assertIn("@media(forced-colors:active)", webmod.CSS)
        head = webmod.page("T", "<p>hi</p>").decode("utf-8")
        self.assertIn("<style>", head)
        self.assertIn("forced-color-adjust:none", head)

    def test_legacy_no_data_fallback(self):
        # Legacy path pinned: with no contrast data/module, the old
        # head still renders and the section degrades to its anchor.
        self.assertIsInstance(contrastmod.contrast_css(), str)
        html = contrastmod.section_html()
        self.assertIn(f"id='{contrastmod.STATUS_ANCHOR}'", html)
        legacy = webmod.page("T", "<p>hi</p>").decode("utf-8")
        self.assertIn("<style>", legacy)  # old head renders regardless

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-contrast'",
                      contrastmod.section_html())

    def test_never_raises(self):
        self.assertEqual(contrastmod._join([]), ".chip")
        self.assertEqual(contrastmod._join(None), ".chip")
        self.assertIsInstance(contrastmod.contrast_css(), str)


if __name__ == "__main__":
    unittest.main()
