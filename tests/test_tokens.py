"""Token-table/README-section parity (I-94)."""
import unittest

from groundwork import palette as palettemod
from groundwork import radius as radiusmod
from groundwork import tokens as tokensmod


class TokensParityTest(unittest.TestCase):
    def test_values_match_real_emitters(self):
        by_name = {t["name"]: t["value"] for t in tokensmod.TOKENS}
        for k, v in palettemod.PALETTE.items():
            self.assertEqual(by_name[k], v)
        for k, v in radiusmod.RADII.items():
            self.assertEqual(by_name[k], v)

    def test_every_token_documented(self):
        section = tokensmod.readme_section()
        for t in tokensmod.TOKENS:
            self.assertIn(f"`{t['name']}`", section)
            self.assertIn(f"`{t['value']}`", section)

    def test_renamed_token_breaks_parity(self):
        renamed = [dict(t) for t in tokensmod.TOKENS]
        renamed[0] = dict(renamed[0], name="--ink-renamed")
        section = tokensmod.readme_section(renamed)
        self.assertIn("--ink-renamed", section)
        self.assertNotIn("`--ink`", section)

    def test_styleguide_covers_same_set(self):
        rows = tokensmod.styleguide_rows()
        for t in tokensmod.TOKENS:
            self.assertIn(t["name"], rows)

    def test_legacy_no_data_path_pinned(self):
        for bad in ([], "nope", 42, {}):
            section = tokensmod.readme_section(bad)
            self.assertIn("| Name | Value | Usage |", section)
            gallery = tokensmod.styleguide_rows(bad)
            self.assertIn("Design tokens", gallery)
            self.assertNotIn("<table", gallery)

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-tokens'",
                      tokensmod.section_html())

    def test_tour_entry_shape(self):
        e = tokensmod.tour_entry()
        self.assertEqual(e["id"], "design-tokens")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b18-tokens")
        self.assertTrue(e["title"] and e["blurb"])


if __name__ == "__main__":
    unittest.main()
