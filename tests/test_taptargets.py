"""44px minimum tap targets (I-66)."""
import unittest

from groundwork import taptargets as tapmod


class TapTargetsTest(unittest.TestCase):
    def test_floor_is_44(self):
        self.assertEqual(tapmod.MIN_PX, 44)

    def test_root_block_with_token(self):
        css = tapmod.target_css()
        self.assertTrue(css.startswith(":root{"))
        self.assertIn("--tap-min:44px", css)

    def test_element_rules_reference_only_variable(self):
        css = tapmod.target_css()
        rules = css.split("}", 1)[1]
        self.assertIn("var(--tap-min)", rules)
        self.assertNotIn("px", rules)
        self.assertNotIn("rem", rules)

    def test_base_covers_buttons_and_inputs(self):
        css = tapmod.target_css()
        for sel in ("button,", "input:not([type=hidden])",
                    "select", "textarea", ".btn"):
            self.assertIn(sel, css)
        self.assertIn("min-height", css)
        self.assertIn("min-width", css)

    def test_compact_reasserts_primary_floor(self):
        css = tapmod.target_css(compact=True)
        self.assertIn("body.density-compact", css)
        self.assertIn("--tap-min:44px", css)
        self.assertNotIn("36px", css)

    def test_compact_off_has_no_density_scope(self):
        self.assertNotIn("density-compact", tapmod.target_css())

    def test_audit_flags_small_inline_control(self):
        findings = tapmod.audit("<button style=\"height:28px\">x</button>")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 1)
        self.assertTrue(findings[0]["element"].startswith("<button"))
        self.assertIn("28px", findings[0]["detail"])
        self.assertIn("44", findings[0]["detail"])

    def test_audit_passes_compliant(self):
        self.assertEqual(
            tapmod.audit("<button style=\"min-height:44px\">x</button>"), [])
        self.assertEqual(
            tapmod.audit("<button style=\"min-height:var(--tap-min)\">x</button>"),
            [])
        self.assertEqual(tapmod.audit("<button>x</button>"), [])

    def test_audit_ignores_hidden_input(self):
        self.assertEqual(
            tapmod.audit("<input type=\"hidden\" style=\"height:1px\">"), [])

    def test_audit_hostile_input_never_raises(self):
        for bad in (None, 5, ["<button>"], ""):
            self.assertEqual(tapmod.audit(bad), [])

    def test_section_html_anchor(self):
        self.assertIn("id='status-b11-taptargets'", tapmod.section_html())

    def test_tour_entry_shape(self):
        entry = tapmod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], tapmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
