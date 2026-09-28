"""Full keyboard answer-rate-advance flow: script, wires, legacy pins (I-200)."""
import json
import unittest

from groundwork import autoscroll as autoscrollmod
from groundwork import cards as cardsmod
from groundwork import keyflow as keyflowmod
from groundwork import results as resmod
from groundwork import web as webmod


def _card():
    return {"id": "c1", "exercise_type": "8", "payload": json.dumps({})}


def _result_body():
    body = resmod.render_result(True, "Nice recall.", "Paris.", "tomorrow",
                                "/due#card-c1", "m1", due_left=3)
    return autoscrollmod.enhance_result(body)


class KeyflowScriptTest(unittest.TestCase):
    def test_rate_keys_cover_confidence_range(self):
        js = keyflowmod.flow_js()
        self.assertIn("altKey", js)
        self.assertIn("confidence", js)
        self.assertIn('"1"', js)
        self.assertIn('"5"', js)

    def test_script_guards_typing_and_modifiers(self):
        js = keyflowmod.flow_js()
        for needle in ("textarea", "isContentEditable", "ctrlKey", "metaKey"):
            self.assertIn(needle, js)

    def test_advance_keys_target_verdict_sibling(self):
        js = keyflowmod.flow_js()
        self.assertIn("verdict", js)
        self.assertIn('"n"', js)
        self.assertIn('"Enter"', js)

    def test_installs_once_with_marker(self):
        js = keyflowmod.flow_js()
        self.assertTrue(js.startswith("<script "))
        self.assertIn(keyflowmod.SCRIPT_MARKER, js)
        self.assertIn("__keyflowInit", js)

    def test_hints_render_only_when_live(self):
        js = keyflowmod.flow_js()
        self.assertIn(keyflowmod.RATE_HINT, js)
        self.assertIn(keyflowmod.NEXT_HINT, js)


class KeyflowEffectTest(unittest.TestCase):
    def test_page_chrome_carries_flow(self):
        shell = webmod.page("T", "<p>x</p>").decode()
        self.assertIn(keyflowmod.SCRIPT_MARKER, shell)
        self.assertIn("__keyflowInit", shell)

    def test_queue_cards_expose_rate_targets(self):
        widget = cardsmod.answer_widget(_card(), 0, "/due")
        for v in ("1", "2", "3", "4", "5"):
            self.assertIn(f"name='confidence' value='{v}'", widget)

    def test_result_screen_exposes_advance_target(self):
        body = _result_body()
        self.assertIn("id='verdict'", body)
        self.assertIn("Continue where you left off", body)
        self.assertIn("a class='btn'", body)


class KeyflowLegacyTest(unittest.TestCase):
    def test_answer_widget_needs_no_keyflow(self):
        widget = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertNotIn("keyflow", widget)
        self.assertNotIn("__keyflowInit", widget)
        self.assertIn("<button>Check prediction</button>", widget)

    def test_result_nav_needs_no_keyflow(self):
        nav = resmod.result_nav("/due#card-c1", "m1")
        self.assertNotIn("keyflow", nav)
        self.assertIn("href='/due#card-c1'", nav)

    def test_submit_shortcut_untouched(self):
        self.assertIn("f.submit()", webmod.GLOBAL_JS)
        self.assertIn("Ctrl/Cmd+Enter", webmod.GLOBAL_JS)


class KeyflowTourTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        entry = keyflowmod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], keyflowmod.STATUS_ANCHOR)

    def test_section_html_anchored(self):
        body = keyflowmod.section_html()
        self.assertIn(f"id='{keyflowmod.STATUS_ANCHOR}'", body)
        self.assertIn("keyflow", body)


if __name__ == "__main__":
    unittest.main()
