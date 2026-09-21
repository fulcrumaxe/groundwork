"""Pass/fail verdict stamps: CSS shapes, still text-readable (I-77)."""
import re
import unittest

from groundwork import verdicts as vmod


def _text_of(html_str):
    return re.sub(r"<[^>]+>", "", html_str)


class VerdictStampTest(unittest.TestCase):
    def test_labels_are_plain_readable_words_never_emoji_or_glyphs(self):
        for passed, want in ((True, "PASS"), (False, "FAIL")):
            stamp = vmod.verdict_stamp(passed)
            self.assertEqual(stamp["label"], want)
            self.assertTrue(stamp["label"].isalpha())
            self.assertEqual(stamp["label"], stamp["label"].upper())
        for stamp in (vmod.verdict_stamp(True), vmod.verdict_stamp(False)):
            self.assertNotIn("✓", stamp["label"])  # check
            self.assertNotIn("✗", stamp["label"])  # cross

    def test_stamp_classes_are_styling_hooks(self):
        self.assertIn("verdict-stamp", vmod.verdict_stamp(True)["cls"])
        self.assertIn("verdict-stamp", vmod.verdict_stamp(False)["cls"])
        self.assertNotEqual(vmod.verdict_stamp(True)["cls"],
                            vmod.verdict_stamp(False)["cls"])

    def test_text_readability_label_present_without_css(self):
        # The verdict words live in markup text, not in CSS content rules.
        for passed, want in ((True, "PASS"), (False, "FAIL")):
            self.assertIn(want, _text_of(vmod.stamp_html(passed)))
        css = vmod.verdicts_css()
        self.assertNotIn("content:", css.replace(" ", ""))
        self.assertNotIn("PASS", css)
        self.assertNotIn("FAIL", css.replace("var(--fail)", ""))

    def test_css_uses_palette_pass_fail_tokens(self):
        css = vmod.verdicts_css()
        self.assertIn("var(--pass)", css)
        self.assertIn("var(--fail)", css)

    def test_css_stamp_look_rotation_double_border_letterspacing(self):
        css = vmod.verdicts_css().replace(" ", "")
        self.assertIn("rotate(", css)
        self.assertIn("letter-spacing:", css)
        self.assertIn("border:", css)  # outer border…
        self.assertIn("outline:", css)  # …plus outline = double border

    def test_reduced_motion_override_unrotates(self):
        css = vmod.verdicts_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("transform:none", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = vmod.verdicts_css().lower()
        self.assertNotIn("<style", css)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, 0, "", object(), [True]):
            stamp = vmod.verdict_stamp(bad)
            self.assertIn(stamp["label"], ("PASS", "FAIL"))
            self.assertIn("verdict-stamp", stamp["cls"])
            self.assertIn(stamp["label"], _text_of(vmod.stamp_html(bad)))
        vmod.verdicts_css()
        vmod.section_html()
        vmod.tour_entry()

    def test_section_html_anchor(self):
        self.assertIn("id='status-b12-verdicts'", vmod.section_html())

    def test_tour_entry_shape(self):
        entry = vmod.tour_entry()
        self.assertEqual(entry["id"], "verdict-stamps")
        self.assertEqual(entry["kind"], "improvement")
        self.assertTrue(entry["title"] and entry["blurb"])
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b12-verdicts")


if __name__ == "__main__":
    unittest.main()
