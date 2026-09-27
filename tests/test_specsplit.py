"""Rebuild spec beside the editor in a split view (I-171)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import codeedit as codeeditmod
from groundwork import emoji as emojimod
from groundwork import runkey as runkeymod
from groundwork import specsplit as mod

SPEC = "Return the sum of two numbers."
SIG = "def add(a, b):"
FRONT = ("Rebuild `add` from this spec alone:\n" + SPEC
         + "\nKeep this interface:\n```python\n" + SIG + "\n```")


def _card(front=FRONT, payload=None, etype=23):
    if payload is None:
        payload = {"spec": SPEC, "signature": SIG, "tests": "",
                   "reference": "x", "grounded": False}
    return {"id": "r23", "exercise_type": etype,
            "payload": json.dumps(payload), "front": front}


def _legacy_body():
    return (codeeditmod.editor_html() + runkeymod.hint_html() + "<br>"
            f"{cardsmod._confidence()}" + runkeymod.run_button_html()
            + codeeditmod.editor_js() + runkeymod.exercise_script_js())


class SpecsplitUnitTest(unittest.TestCase):
    def test_parse_spec_prefers_payload(self):
        spec, sig = mod.parse_spec("ignored",
                                   {"spec": SPEC, "signature": SIG})
        self.assertEqual((spec, sig), (SPEC, SIG))

    def test_parse_spec_falls_back_to_front(self):
        spec, sig = mod.parse_spec(FRONT, {})
        self.assertEqual(spec, SPEC)
        self.assertEqual(sig, SIG)

    def test_parse_spec_fails_closed(self):
        self.assertEqual(mod.parse_spec("", {}), ("", ""))
        self.assertEqual(mod.parse_spec(None, None), ("", ""))
        self.assertEqual(mod.parse_spec("   ", {"spec": ""}), ("", ""))

    def test_parse_spec_truncates_long_spec(self):
        spec, _ = mod.parse_spec("", {"spec": "x" * 5000,
                                      "signature": SIG})
        self.assertEqual(len(spec), mod.MAX_SPEC_CHARS)

    def test_pane_escapes_spec_and_signature(self):
        out = mod.spec_pane_html("<b>bold</b>", "<code>")
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("&lt;code&gt;", out)
        self.assertIn("Keep this interface", out)

    def test_pane_blank_is_empty(self):
        self.assertEqual(mod.spec_pane_html("", ""), "")
        self.assertEqual(mod.spec_pane_html(None, None), "")

    def test_css_has_no_style_tag(self):
        self.assertNotIn("<style>", mod.split_css())
        self.assertIn(".spsplit-edit", mod.split_css())


class SpecsplitEffectTest(unittest.TestCase):
    def test_caller_widget_gains_spec_split(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("spsplit", out)
        self.assertIn("Return the sum", out)
        self.assertIn("def add", out)
        self.assertIn("name='answer'", out)

    def test_caller_widget_no_spec_is_byte_identical_legacy(self):
        card = _card(front="plain front", payload={})
        self.assertEqual(mod.branch_html(card, {}, "r23"),
                         _legacy_body())
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("spsplit", out)
        self.assertIn("codeedit", out)

    def test_other_code_types_untouched(self):
        card = _card(etype=19)
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("spsplit", out)
        self.assertIn("codeedit", out)


class SpecsplitShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
