"""Dark mode overrides + contrast (I-52)."""
import re
import unittest

from groundwork import darkmode as darkmod
from groundwork import palette as palettemod


class DarkmodeTest(unittest.TestCase):
    def test_every_token_overridden_no_strays(self):
        self.assertEqual(set(darkmod.DARK_OVERRIDES),
                         set(palettemod.PALETTE))

    def test_dark_values_differ_from_light(self):
        for token, dark in darkmod.DARK_OVERRIDES.items():
            self.assertNotEqual(dark.lower(),
                                palettemod.PALETTE[token].lower(),
                                token)

    def test_aa_pairs_pass(self):
        self.assertEqual(darkmod.check_contrast(), [])
        for fg_token, bg_token in darkmod.AA_PAIRS:
            fg = darkmod._resolve(fg_token)
            bg = darkmod._resolve(bg_token)
            self.assertGreaterEqual(darkmod.contrast_ratio(fg, bg), 4.5,
                                    f"{fg_token} on {bg_token}")

    def test_contrast_math_sanity(self):
        self.assertAlmostEqual(
            darkmod.contrast_ratio("#ffffff", "#000000"), 21.0, places=1)
        self.assertAlmostEqual(
            darkmod.contrast_ratio("#123456", "#123456"), 1.0, places=6)
        with self.assertRaises(ValueError):
            darkmod.luminance("not-a-color")

    def test_dark_css_is_variable_only_reassignment(self):
        css = darkmod.dark_css()
        self.assertIn("@media (prefers-color-scheme: dark)", css)
        self.assertEqual(css.count("{"), 2)  # media + :root, no selectors
        self.assertIn(":root{", css)
        body = css.split(":root{", 1)[1].rstrip("}")
        decls = [d for d in body.split(";") if d]
        names = []
        for decl in decls:
            m = re.fullmatch(r"(--[\w-]+):(#[0-9a-fA-F]{6})", decl)
            self.assertIsNotNone(m, decl)
            names.append(m.group(1))
        self.assertEqual(set(names), set(palettemod.PALETTE))
        for token in palettemod.PALETTE:
            self.assertIn(f"{token}:{darkmod.DARK_OVERRIDES[token]}", css)

    def test_section_html_anchor(self):
        html = darkmod.section_html()
        self.assertIn("id='status-b9-darkmode'", html)


if __name__ == "__main__":
    unittest.main()
