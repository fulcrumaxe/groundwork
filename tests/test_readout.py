"""Code-reading-aloud mode for walkthrough steps (I-138)."""
import unittest

from groundwork import readout as mod
from groundwork import web as webmod

from test_web import handler_for, make_module


class ScriptTest(unittest.TestCase):
    def test_guards_speech_support(self):
        js = mod.script_js()
        self.assertIn("data-readaloud", js)
        self.assertIn("speechSynthesis", js)
        self.assertIn("if(!('speechSynthesis' in window))return;", js)

    def test_click_toggles_stop(self):
        js = mod.script_js()
        self.assertIn("speaking", js)
        self.assertIn("cancel()", js)

    def test_targets_replay_blocks(self):
        js = mod.script_js()
        self.assertIn("querySelectorAll('.replay')", js)
        self.assertIn(mod.BUTTON_CLASS, js)
        self.assertIn(mod.BUTTON_LABEL, js)

    def test_sample_matches_injected_button(self):
        sample = mod.sample_button_html()
        self.assertIn(f"class='{mod.BUTTON_CLASS}'", sample)
        self.assertIn(mod.BUTTON_LABEL, sample)
        self.assertIn(f"b.className='{mod.BUTTON_CLASS}'", mod.script_js())

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "reading-aloud", "kind": "improvement",
            "title": "Reading aloud",
            "blurb": ("Walkthrough steps grow a Listen button — the "
                      "trace, spoken."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_every_page_carries_wire(self):
        raw = webmod.page("T", "<p>x</p>").decode()
        self.assertIn("data-readaloud", raw)

    def test_module_body_byte_identical_without_js(self):
        _tmp, db, _s, out = make_module("readout caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("readaloud", body)


if __name__ == "__main__":
    unittest.main()
