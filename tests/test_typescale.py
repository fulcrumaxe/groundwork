"""Modular type scale (I-53)."""
import unittest

from groundwork import typescale as typescalemod

EXPECTED_STEPS = ("display", "h1", "h2", "h3", "h4", "body", "small", "code")

CHAIN = ("small", "body", "h4", "h3", "h2", "h1", "display")


class TypescaleTest(unittest.TestCase):
    def test_every_step_present(self):
        for step in EXPECTED_STEPS:
            self.assertIn(step, typescalemod.STEPS)
        self.assertEqual(len(typescalemod.STEPS), len(EXPECTED_STEPS))

    def test_ratio_consistency(self):
        for lower, upper in zip(CHAIN, CHAIN[1:]):
            self.assertEqual(
                typescalemod.STEPS[upper],
                round(typescalemod.STEPS[lower] * typescalemod.RATIO, 2),
                f"{upper} is not one ratio step above {lower}")
        self.assertEqual(typescalemod.STEPS["code"],
                         typescalemod.STEPS["small"])

    def test_root_block_with_all_tokens(self):
        css = typescalemod.scale_css()
        self.assertTrue(css.startswith(":root{"))
        for step in EXPECTED_STEPS:
            self.assertIn(f"--fs-{step}:", css)

    def test_element_rules_reference_only_variables(self):
        css = typescalemod.scale_css()
        rules = css.split("}", 1)[1]
        # Element steps get rules; display is variable-only (no
        # <display> element exists — pages use var(--fs-display)).
        for step in ("h1", "h2", "h3", "h4", "body", "small", "code"):
            self.assertIn(f"var(--fs-{step})", rules)
        for sel in ("h1{", "h2{", "h3{", "h4{", "body{",
                    "small{", "code,pre{"):
            self.assertIn(sel, rules)
        self.assertNotIn("px", rules)
        self.assertNotIn("rem", rules)

    def test_display_is_variable_only(self):
        css = typescalemod.scale_css()
        self.assertIn("--fs-display:", css.split("}", 1)[0])
        self.assertNotIn("var(--fs-display)", css.split("}", 1)[1])

    def test_px_for_lookup(self):
        self.assertEqual(typescalemod.px_for("h1"),
                         typescalemod.STEPS["h1"])
        self.assertEqual(typescalemod.px_for("body"),
                         typescalemod.BASE_PX)

    def test_px_for_fallback_never_raises(self):
        body = typescalemod.STEPS["body"]
        self.assertEqual(typescalemod.px_for("h9"), body)
        self.assertEqual(typescalemod.px_for(""), body)
        self.assertEqual(typescalemod.px_for(None), body)
        self.assertEqual(typescalemod.px_for(["h1"]), body)
        self.assertEqual(typescalemod.px_for({"step": "h1"}), body)


if __name__ == "__main__":
    unittest.main()
