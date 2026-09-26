"""Live rubric checklist beside explain textareas (I-167)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import rubriclive as mod


def _card(etype, rubric=None):
    payload = {} if rubric is None else {"rubric": rubric}
    return {"id": "e1", "exercise_type": etype,
            "payload": json.dumps(payload)}


class RubricliveUnitTest(unittest.TestCase):
    def test_rubric_for_parses_json_payload(self):
        self.assertEqual(mod.rubric_for(_card(5, ["loop", "exit"])),
                         ["loop", "exit"])

    def test_rubric_for_empty_on_bad_input(self):
        self.assertEqual(mod.rubric_for(_card(5)), [])
        self.assertEqual(mod.rubric_for({"id": "x"}), [])
        self.assertEqual(mod.rubric_for(None), [])
        self.assertEqual(
            mod.rubric_for({"id": "x", "payload": "{bad"}), [])

    def test_matched_is_case_insensitive_word_bounded(self):
        self.assertEqual(mod.matched("the Loop runs", ["loop"]), [True])
        self.assertEqual(mod.matched("sloop", ["loop"]), [False])
        self.assertEqual(mod.matched("exit early", ["exit early"]), [True])
        self.assertEqual(mod.matched("x", []), [])
        self.assertEqual(mod.matched(None, ["a"]), [False])

    def test_checklist_renders_unchecked_and_escapes(self):
        out = mod.checklist_html("e1", ["loop", "<script>"])
        self.assertEqual(out.count("[ ]"), 2)
        self.assertNotIn("[x]", out)
        self.assertIn("data-kw='loop'", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)

    def test_checklist_empty_is_empty(self):
        self.assertEqual(mod.checklist_html("e1", []), "")
        self.assertEqual(mod.checklist_html("e1", None), "")

    def test_script_ticks_on_input(self):
        js = mod.script_js()
        self.assertIn("__rubricliveInit", js)
        self.assertIn("textarea[name=answer]", js)


class RubricliveEffectTest(unittest.TestCase):
    def test_explain_widget_gains_checklist_with_rubric(self):
        out = cardsmod.answer_widget(_card(5, ["loop"]), 0, "/due")
        self.assertIn("rubriclive", out)
        self.assertIn("[ ]", out)
        self.assertIn("__rubricliveInit", out)

    def test_explain_widget_no_rubric_is_legacy(self):
        out = cardsmod.answer_widget(_card(5), 0, "/due")
        self.assertNotIn("rubriclive", out)
        self.assertIn("<textarea name='answer'", out)

    def test_choice_type_untouched(self):
        card = {"id": "c4", "exercise_type": 4,
                "payload": json.dumps({"choices": ["a", "b"]})}
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("rubriclive", out)

    def test_type22_excluded_despite_rubric(self):
        out = cardsmod.answer_widget(_card(22, ["loop"]), 0, "/due")
        self.assertNotIn("rubriclive", out)

    def test_plugin_explain_branch_gains_checklist(self):
        out = cardsmod.answer_widget(_card(83, ["why"]), 0, "/due")
        self.assertIn("rubriclive", out)

    def test_enhance_row_safe(self):
        class Row(dict):
            def get(self, *a, **k):
                raise AttributeError("Rows have no .get")
        row = Row(id="e9", exercise_type=5,
                  payload=json.dumps({"rubric": ["loop"]}))
        out = mod.enhance(row, "<textarea name='answer'></textarea>")
        self.assertIn("rubriclive", out)


class RubricliveShapeTest(unittest.TestCase):
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
