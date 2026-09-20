"""Keyboard shortcuts: overlay, script, and shell wiring (I-40)."""
import unittest

from groundwork import shortcuts as shortcutsmod
from groundwork import web as webmod


class ShortcutsTest(unittest.TestCase):
    def test_shortcut_keys_unique(self):
        keys = [k for k, _, _ in shortcutsmod.SHORTCUTS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(keys)

    def test_overlay_lists_every_shortcut(self):
        body = shortcutsmod.overlay_html()
        self.assertIn("id='shortcuts'", body)
        for keys, label, _ in shortcutsmod.SHORTCUTS:
            self.assertIn(label, body)

    def test_script_guards_typing_and_covers_targets(self):
        js = shortcutsmod.script_js()
        self.assertIn("keydown", js)
        self.assertIn("textarea", js)
        for _, _, href in shortcutsmod.SHORTCUTS:
            if href:
                self.assertIn(href, js)

    def test_every_page_carries_overlay(self):
        shell = webmod.page("T", "<p>x</p>").decode()
        self.assertIn("id='shortcuts'", shell)
        self.assertIn("keydown", shell)


if __name__ == "__main__":
    unittest.main()
