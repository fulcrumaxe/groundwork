"""Section spacing scale (I-68)."""
import unittest

from groundwork import spacing as spacingmod

EXPECTED_STEPS = ("tight", "snug", "section", "roomy", "page", "airy", "display")
CHAIN = ("tight", "snug", "section", "roomy", "page", "airy", "display")


class SpacingTest(unittest.TestCase):
    def test_every_step_present(self):
        for step in EXPECTED_STEPS:
            self.assertIn(step, spacingmod.STEPS)
        self.assertEqual(len(spacingmod.STEPS), len(EXPECTED_STEPS))

    def test_ratio_consistency(self):
        for lower, upper in zip(CHAIN, CHAIN[1:]):
            self.assertEqual(
                spacingmod.STEPS[upper],
                round(spacingmod.STEPS[lower] * spacingmod.RATIO, 3),
                f"{upper} is not one ratio step above {lower}")

    def test_section_step_is_base(self):
        self.assertEqual(spacingmod.STEPS["section"], spacingmod.BASE_REM)

    def test_root_block_with_all_tokens(self):
        css = spacingmod.spacing_css()
        self.assertTrue(css.startswith(":root{"))
        for step in EXPECTED_STEPS:
            self.assertIn(f"--sp-{step}:", css)

    def test_rhythm_rules_reference_only_variables(self):
        css = spacingmod.spacing_css()
        rules = css.split("}", 1)[1]
        for step in EXPECTED_STEPS:
            self.assertIn(f"var(--sp-{step})", rules)
        self.assertNotIn("rem", rules)
        self.assertNotIn("px", rules)

    def test_rem_for_lookup(self):
        self.assertEqual(spacingmod.rem_for("page"), spacingmod.STEPS["page"])

    def test_rem_for_fallback_never_raises(self):
        base = spacingmod.STEPS["section"]
        for bad in ("h9", "", None, ["page"], {"step": "page"}):
            self.assertEqual(spacingmod.rem_for(bad), base)

    def test_rhythm_for_roles(self):
        self.assertEqual(spacingmod.rhythm_for("page-head"), "page")
        self.assertEqual(spacingmod.rhythm_for("card"), "snug")
        self.assertEqual(spacingmod.rhythm_for("SECTION"), "section")

    def test_rhythm_for_fallback_never_raises(self):
        for bad in ("banner-typo", "", None, ["section"], {"r": 1}):
            self.assertEqual(spacingmod.rhythm_for(bad), "section")

    def test_apply_rhythm_tags_bare_sections(self):
        out = spacingmod.apply_rhythm("<section><p>x</p></section>")
        self.assertIn("rhythm-section", out)
        self.assertIn("<p>x</p>", out)

    def test_apply_rhythm_keeps_attributes(self):
        out = spacingmod.apply_rhythm("<section id='s'>", "hero")
        self.assertIn("rhythm-display", out)
        self.assertIn("id='s'", out)

    def test_apply_rhythm_leaves_rhythmed_alone(self):
        src = "<section class='rhythm-page'>"
        self.assertEqual(spacingmod.apply_rhythm(src, "hero"), src)

    def test_apply_rhythm_ignores_lookalikes(self):
        self.assertEqual(spacingmod.apply_rhythm("<sections>"), "<sections>")

    def test_apply_rhythm_non_string(self):
        self.assertEqual(spacingmod.apply_rhythm(None), "")

    def test_audit_sections(self):
        src = "<section><section class='rhythm-page'>"
        self.assertEqual(spacingmod.audit_sections(src),
                         {"total": 2, "rhythmed": 1, "bare": 1})
        self.assertEqual(spacingmod.audit_sections(None),
                         {"total": 0, "rhythmed": 0, "bare": 0})

    def test_status_anchor(self):
        self.assertEqual(spacingmod.STATUS_ANCHOR, "status-b11-spacing")
        self.assertIn("status-b11-spacing", spacingmod.section_html())


if __name__ == "__main__":
    unittest.main()
