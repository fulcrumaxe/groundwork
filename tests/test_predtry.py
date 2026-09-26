"""Predict-output pre-submit retries: 3 strikes, shrinking hints (I-166)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import predtry as mod


def _card(payload):
    return {"id": "p8", "exercise_type": 8, "payload": json.dumps(payload)}


class PredtryHintTest(unittest.TestCase):
    def test_tier1_shape(self):
        self.assertEqual(mod.hint_for("a\nb", "zzz", 1),
                         "Expected 2 line(s), 3 char(s).")

    def test_tier2_position(self):
        self.assertEqual(mod.tier2_position("a\nb", "a\nB"), (2, 1))
        self.assertIn("line 2, char 1",
                      mod.hint_for("a\nb", "a\nB", 2))

    def test_tier3_region_quotes_expected(self):
        out = mod.hint_for("hello world", "hello WORLD", 3)
        self.assertIn("Near miss", out)
        self.assertIn("hello world", out)

    def test_match_gives_no_hint(self):
        for n in (1, 2, 3):
            self.assertEqual(mod.hint_for("a", "a", n), "")

    def test_bad_strikes_and_hostile(self):
        self.assertEqual(mod.hint_for("a", "b", 0), "")
        self.assertEqual(mod.hint_for("a", "b", 4), "")
        self.assertEqual(mod.hint_for(None, None, 1), "")
        self.assertEqual(mod.tier1_shape(None), "")
        self.assertIsNone(mod.tier2_position(None, None))


class PredtryWidgetTest(unittest.TestCase):
    def test_tries_html_present_with_reference(self):
        out = mod.tries_html(_card({"code": "print(1)", "expected": "1"}))
        self.assertIn("Try without submitting", out)
        self.assertIn("data-expected", out)
        self.assertIn("__predtry", out)
        self.assertIn("input[name=answer]", out)

    def test_tries_html_empty_without_reference(self):
        self.assertEqual(mod.tries_html(_card({"code": "x"})), "")
        self.assertEqual(mod.tries_html({}), "")
        self.assertEqual(mod.tries_html(None), "")

    def test_tries_html_escapes_reference(self):
        out = mod.tries_html(
            _card({"code": "print(1)", "expected": "a'b\"c"}))
        self.assertIn("a&#x27;b&quot;c", out)

    def test_caller_widget_gains_affordance(self):
        out = cardsmod.answer_widget(
            _card({"code": "print(1)", "expected": "1"}), 0, "/due")
        self.assertIn("predtry", out)

    def test_caller_widget_no_reference_is_legacy(self):
        out = cardsmod.answer_widget(_card({"code": "print(1)"}), 0, "/due")
        self.assertNotIn("predtry", out)

    def test_choices_branch_reads_typed_input(self):
        out = cardsmod.answer_widget(
            _card({"code": "print(1)", "expected": "1",
                   "choices": ["1", "2"]}), 0, "/due")
        self.assertIn("predtry", out)
        self.assertIn("Type it:", out)


class PredtryShapeTest(unittest.TestCase):
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
