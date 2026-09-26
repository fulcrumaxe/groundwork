"""Run button with Ctrl+Enter hint on code exercises (I-155)."""
import unittest

from groundwork import cards as cardsmod
from groundwork import runkey as runkeymod


def _code_card(etype="12"):
    return {"id": "7", "exercise_type": etype, "payload": "{}"}


class RunkeyTest(unittest.TestCase):
    def test_code_types_covered(self):
        for etype in ("12", "14", "19", "20", "23"):
            self.assertTrue(runkeymod.is_code_exercise(etype))
            self.assertTrue(runkeymod.is_code_exercise(int(etype)))

    def test_non_code_types_excluded(self):
        for etype in ("1", "2", "4", "5", "8", "9", "10", "11", "99", "", None):
            self.assertFalse(runkeymod.is_code_exercise(etype))
            self.assertEqual("", runkeymod.runkey_for(etype))

    def test_button_labels_shortcut(self):
        body = runkeymod.run_button_html()
        self.assertIn("Run tests", body)
        self.assertIn("data-runkey", body)
        self.assertIn("Ctrl+Enter", body)
        self.assertIn("type='submit'", body)

    def test_button_escapes_label(self):
        body = runkeymod.run_button_html("<b>x</b>")
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_button_falls_back_on_blank_label(self):
        self.assertIn("Run tests", runkeymod.run_button_html(""))
        self.assertIn("Run tests", runkeymod.run_button_html(None))

    def test_hint_names_shortcut(self):
        hint = runkeymod.hint_html()
        self.assertIn("Ctrl+Enter", hint)
        self.assertIn("Cmd+Enter", hint)

    def test_script_scoped_to_runkey_forms(self):
        js = runkeymod.exercise_script_js()
        self.assertIn("keydown", js)
        self.assertIn("data-runkey", js)
        self.assertIn("ctrlKey", js)
        self.assertIn("metaKey", js)
        self.assertIn("textarea", js)
        # One listener per page even with N code cards on it.
        self.assertIn("__runkeyInit", js)

    def test_runkey_for_bundles_button_hint_script(self):
        body = runkeymod.runkey_for("12")
        self.assertIn("data-runkey", body)
        self.assertIn("runkey-hint", body)
        self.assertIn("keydown", body)

    def test_section_html_anchored(self):
        body = runkeymod.section_html()
        self.assertIn(f"id='{runkeymod.STATUS_ANCHOR}'", body)
        self.assertIn("runkey.py", body)
        self.assertIn("data-runkey", body)

    def test_tour_entry_shape(self):
        entry = runkeymod.tour_entry()
        self.assertEqual("improvement", entry["kind"])
        for key in ("id", "title", "blurb", "path", "anchor"):
            self.assertTrue(entry[key])


class EffectTest(unittest.TestCase):
    def test_caller_widget_renders_run_button(self):
        body = cardsmod.answer_widget(_code_card())
        self.assertIn("data-runkey", body)
        self.assertIn("<kbd>Ctrl+Enter</kbd>", body)
        self.assertIn("runkey-hint", body)
        self.assertIn("name='answer'", body)

    def test_non_code_cards_untouched(self):
        body = cardsmod.answer_widget({"id": "7", "exercise_type": "1",
                                       "payload": "{}"})
        self.assertNotIn("data-runkey", body)
        self.assertNotIn("runkey-hint", body)


if __name__ == "__main__":
    unittest.main()
