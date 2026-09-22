"""Tests for the emoji-as-icon scanner and replacements (I-97)."""
import unittest

from groundwork import emoji as mod


class PolicyTest(unittest.TestCase):
    def test_blocked_glyphs(self):
        for glyph in ("✓", "✗", "★", "☆", "⠿", "↑", "↓", "←",
                      "\U0001F3C6", "\U00002705", "\u200d", "↗"):
            self.assertTrue(mod.is_blocked(glyph), glyph)

    def test_prose_arrow_allowed(self):
        self.assertFalse(mod.is_blocked("→"))
        self.assertEqual(mod.scan_text("a → b"), [])

    def test_plain_text_clean(self):
        self.assertEqual(mod.scan_text("PASS"), [])
        self.assertEqual(mod.scan_text("Back to top"), [])


class EffectTest(unittest.TestCase):
    def test_flags_planted_emoji_fixture(self):
        # Behavioral effect: a planted raw-emoji line is caught.
        fixture = ("<p class='ok'>✓ grade 5/5</p>\n"
                   "<button type='button' data-move='-1'>↑</button>")
        hits = mod.scan_html(fixture)
        codes = {h["codepoint"] for h in hits}
        self.assertIn("U+2713", codes)
        self.assertIn("U+2191", codes)

    def test_tree_scans_clean_after_cleanup(self):
        # CI gate: fails on ANY new raw emoji in shipped source.
        self.assertEqual(mod.scan_tree("groundwork"), [])


class LegacyFallbackTest(unittest.TestCase):
    def test_no_data_scans_clean_never_raises(self):
        for bad in (None, "", 0, ["✓"], object(), {"t": "✓"}):
            self.assertEqual(mod.scan_text(bad), [])
            self.assertEqual(mod.scan_html(bad), [])
        self.assertEqual(mod.scan_tree("/nonexistent-dir"), [])
        self.assertEqual(mod.scan_file("/nonexistent.py"), [])
        self.assertFalse(mod.is_blocked(""))
        self.assertFalse(mod.is_blocked("✓x"))

    def test_helpers_fail_closed_never_raise(self):
        self.assertIsInstance(mod.move_button(None, None), str)
        self.assertIn("Move down", mod.move_button(None, None))
        self.assertIsInstance(mod.grip_html(), str)
        self.assertIsInstance(mod.totop_html(), str)
        self.assertIsInstance(mod.icon_css(), str)
        self.assertIsInstance(mod.section_html(), str)


class ReplacementTest(unittest.TestCase):
    def test_css_ascii_no_blocked_no_style_tags(self):
        css = mod.icon_css()
        self.assertTrue(css.isascii())
        self.assertEqual(mod.scan_text(css), [])
        self.assertNotIn("<style", css.lower())
        for cls in (".grip", ".move-btn", ".totop::after",
                    ".reviewed-tick::before", ".ext-marker",
                    "prefers-reduced-motion"):
            self.assertIn(cls, css)

    def test_move_button_labels_readable_without_css(self):
        up = mod.move_button("up", "c1")
        down = mod.move_button("down", "c1")
        self.assertIn("Move up", up)
        self.assertIn("Move down", down)
        self.assertIn("aria-label", up)
        self.assertEqual(mod.scan_text(up + down), [])

    def test_totop_grip_have_no_glyphs(self):
        for blob in (mod.totop_html(), mod.grip_html()):
            self.assertEqual(mod.scan_text(blob), [])
        self.assertIn("Back to top", mod.totop_html())


class RenderStatusTest(unittest.TestCase):
    def test_status_anchor(self):
        self.assertIn("id='status-b18-emoji'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "emoji-free-icons")
        self.assertEqual(t["kind"], "improvement")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b18-emoji")


if __name__ == "__main__":
    unittest.main()
