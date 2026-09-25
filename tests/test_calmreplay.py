"""Calm walkthrough reveals for reduced motion (I-140)."""
import unittest

from groundwork import calmreplay as mod
from groundwork import lessons as lesmod
from groundwork import web as webmod

from test_web import make_module


def _traced_lesson():
    return {"name": "add", "kind": "function", "summary": "Adds.",
            "docstring": "Return a + b.", "how": ["Sets total.", "Adds."],
            "file": "calc.py", "line": 1, "callers": [], "callees": [],
            "worked": {"trace": {"steps": ["1", "3"]}}}


class InstantTest(unittest.TestCase):
    def test_full_trace_hidden(self):
        body = mod.instant_html(_traced_lesson())
        self.assertIn("id='replay-full'", body)
        self.assertIn("hidden", body)
        self.assertIn("all 2 steps", body)
        self.assertIn("Sets total.", body)
        self.assertIn("Adds.", body)

    def test_traceless_empty_is_legacy(self):
        self.assertEqual(mod.instant_html({}), "")
        self.assertEqual(mod.instant_html(None), "")
        self.assertEqual(
            mod.instant_html({"name": "x", "how": ["a"]}), "")

    def test_script_swaps_on_reduced_motion(self):
        js = mod.script_js()
        self.assertIn("data-calm-replay", js)
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("removeAttribute('hidden')", js)
        self.assertIn(".replay-full[hidden]", js)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "calm-reveals", "kind": "improvement",
            "title": "Calm walkthrough reveals",
            "blurb": ("Reduced-motion learners get the whole trace at "
                      "once — no stepping required."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_render_levels_twins_trace(self):
        lesson = _traced_lesson()
        body = lesmod.render_levels(lesson, 0.0, 0, "auto", "/m")
        self.assertIn("id='replay'", body)
        self.assertIn("id='replay-full' hidden", body)

    def test_traceless_lessons_untouched(self):
        _tmp, db, _s, out = make_module("calmreplay legacy")
        body = lesmod.render_levels({"name": "add", "kind": "function",
                                     "summary": "s", "docstring": "d",
                                     "how": ["a"], "file": "f", "line": 1,
                                     "callers": [], "callees": []},
                                    0.0, 0, "auto", "/m")
        self.assertNotIn("replay-full", body)

    def test_every_page_carries_wire(self):
        raw = webmod.page("T", "<p>x</p>").decode()
        self.assertIn("data-calm-replay", raw)


if __name__ == "__main__":
    unittest.main()
