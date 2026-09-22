"""Per-tier Bloom chip colors (I-56)."""
import unittest

from groundwork import bloomchips as bloommod
from groundwork import pipeline as pipelinemod


class BloomChipsTest(unittest.TestCase):
    TIERS = ("recall", "explain", "apply", "analyse", "modify",
             "evaluate", "create", "understand")  # Batch 18 adds understand

    def test_covers_every_pipeline_tier(self):
        self.assertEqual(set(bloommod.BLOOM_COLORS), set(self.TIERS))
        self.assertEqual(set(bloommod.BLOOM_COLORS),
                         set(pipelinemod.BLOOM_DEFAULT_TYPES))

    def test_entries_hold_light_and_dark_pairs(self):
        for tier, entry in bloommod.BLOOM_COLORS.items():
            for key in ("bg", "fg", "dark_bg", "dark_fg"):
                self.assertIn(key, entry)
                self.assertRegex(entry[key], r"^#[0-9a-f]{6}$")

    def test_css_references_each_tier(self):
        css = bloommod.chip_css()
        for tier in self.TIERS:
            self.assertIn(f".chip.bloom-{tier}", css)
            self.assertIn(f"var(--bloom-{tier})", css)
            self.assertIn(f"var(--bloom-{tier}-fg)", css)

    def test_css_dark_block_reassigns_same_tokens(self):
        css = bloommod.chip_css()
        head, _, dark = css.partition("@media")
        self.assertTrue(dark)
        for tier in self.TIERS:
            self.assertIn(f"--bloom-{tier}:", head)
            self.assertIn(f"--bloom-{tier}:", dark)

    def test_no_style_tags_and_ascii_only(self):
        css = bloommod.chip_css()
        self.assertNotIn("<style", css.lower())
        self.assertTrue(css.isascii())
        html = bloommod.section_html()
        self.assertNotIn("<style", html.lower())

    def test_chip_class_known_and_unknown(self):
        self.assertEqual(bloommod.chip_class("recall"), "chip bloom-recall")
        self.assertEqual(bloommod.chip_class("  ANALYSE "),
                         "chip bloom-analyse")
        for bad in ("nonsense", "", None, 5, ["recall"], object()):
            self.assertEqual(bloommod.chip_class(bad), "chip")

    def test_chip_html_escapes_label(self):
        out = bloommod.chip_html("recall", "<b>x</b>")
        self.assertNotIn("<b>x</b>", out)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", out)
        self.assertIn("chip bloom-recall", out)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, 5, ["recall"], object()):
            bloommod.tier_key(bad)
            bloommod.color_for(bad)
            bloommod.chip_class(bad)
            bloommod.chip_html(bad)
        bloommod.chip_css()
        bloommod.section_html()

    def test_section_html_anchor(self):
        html = bloommod.section_html()
        self.assertIn("id='status-b10-bloomchips'", html)


if __name__ == "__main__":
    unittest.main()
