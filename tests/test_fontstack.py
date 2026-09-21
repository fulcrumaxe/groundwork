"""Distinctive offline-safe font pairing (I-54)."""
import unittest

from groundwork import fontstack as fontmod


class FontStackTest(unittest.TestCase):
    def test_stacks_end_in_generic_family(self):
        self.assertEqual(fontmod.HEADING_STACK[-1], "serif")
        self.assertEqual(fontmod.BODY_STACK[-1], "sans-serif")
        self.assertEqual(fontmod.MONO_STACK[-1], "monospace")

    def test_stacks_are_nonempty_str_tuples(self):
        for stack in (fontmod.HEADING_STACK, fontmod.BODY_STACK,
                      fontmod.MONO_STACK):
            self.assertIsInstance(stack, tuple)
            self.assertGreater(len(stack), 1)
            for name in stack:
                self.assertIsInstance(name, str)
                self.assertTrue(name.strip())

    def test_root_block_with_all_tokens(self):
        css = fontmod.stack_css()
        self.assertTrue(css.startswith(":root{"))
        for token in ("--font-heading", "--font-body", "--font-mono"):
            self.assertIn(token, css)

    def test_element_rules_reference_variables_not_families(self):
        css = fontmod.stack_css()
        root, _, rules = css.partition("}")
        for var in ("var(--font-body)", "var(--font-heading)",
                    "var(--font-mono)"):
            self.assertIn(var, rules)

    def test_no_sizes_no_network_references(self):
        # Sizes belong to typescale.py; families never come from the net.
        css = fontmod.stack_css().lower()
        self.assertNotIn("font-size", css)
        for marker in ("http", "url(", "@import", "@font-face", "system-ui"):
            self.assertNotIn(marker, css)

    def test_stack_for_known_roles(self):
        self.assertEqual(fontmod.stack_for("heading"), fontmod.HEADING_STACK)
        self.assertEqual(fontmod.stack_for("body"), fontmod.BODY_STACK)
        self.assertEqual(fontmod.stack_for("mono"), fontmod.MONO_STACK)
        self.assertEqual(fontmod.stack_for("  MONO "), fontmod.MONO_STACK)

    def test_stack_for_fails_closed_never_raises(self):
        for bad in ("sidebar", "", None, 5, ["mono"], object()):
            self.assertEqual(fontmod.stack_for(bad), fontmod.BODY_STACK)

    def test_stack_font_ends_with_generic(self):
        self.assertTrue(fontmod.stack_font("heading").endswith("serif"))
        self.assertTrue(fontmod.stack_font("body").endswith("sans-serif"))
        self.assertTrue(fontmod.stack_font("mono").endswith("monospace"))
        self.assertIn('"Palatino Linotype"', fontmod.stack_font("heading"))

    def test_section_html_anchor(self):
        html = fontmod.section_html()
        self.assertIn("id='status-b9-fontstack'", html)


if __name__ == "__main__":
    unittest.main()
