"""Protege-effect studio (type 84, F-80)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod
from groundwork import protege as promod


class _Concept:
    node_id = "calc.py:add"
    name = "add"
    kind = "function"
    file = "calc.py"
    line = 1


def _ctx():
    return {"commit": "abc"}


def _card():
    return promod.generate("ex001", _Concept(),
                           ["def add(a, b):", "    return a + b"], _ctx())


def _key(card):
    return card["payload"]["key"]


class GenerateTest(unittest.TestCase):
    def test_grounds_and_stages_junior_plus_followup(self):
        card = _card()
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (84, "protege-studio", "create"))
        self.assertTrue(card["payload"]["grounded"])
        self.assertIn(card["payload"]["junior_claim"], card["front"])
        self.assertEqual(len(card["payload"]["followup"]["choices"]), 3)
        self.assertIn(_key(card), "ABC")

    def test_alias(self):
        a = promod.generate("e1", _Concept(), ["x = 1"], _ctx())
        b = promod.gen_protege("e1", _Concept(), ["x = 1"], _ctx())
        self.assertEqual(a, b)

    def test_never_none(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _Concept(), [], {})]:
            card = promod.generate(*args)
            self.assertIsNotNone(card)
            self.assertTrue(card["front"] and card["back"])

    def test_thin_input_ungrounded(self):
        card = promod.generate("ex9", _Concept(), [], _ctx())
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = promod.generate("e1", _Concept(), ["def f():", "    pass"], _ctx())
        b = promod.generate("e1", _Concept(), ["def f():", "    pass"], _ctx())
        self.assertEqual(a, b)


class GradeTest(unittest.TestCase):
    def test_both_halves_pass(self):
        card = _card()
        ans = " ".join(card["payload"]["rubric"]) + f"\n{_key(card)}"
        res = exmod.grade(card, ans)
        self.assertTrue(res["pass"])

    def test_each_half_can_fail(self):
        card = _card()
        key = _key(card)
        # Correction thin, letter right.
        res = exmod.grade(card, f"nothing relevant\n{key}")
        self.assertFalse(res["pass"])
        self.assertIn("correction", res["feedback"])
        # Correction full, letter wrong.
        wrong = "B" if key != "B" else "C"
        ans = " ".join(card["payload"]["rubric"]) + f"\n{wrong}"
        res = exmod.grade(card, ans)
        self.assertFalse(res["pass"])
        self.assertIn(key, res["feedback"])

    def test_keyed_letter_form(self):
        card = _card()
        ans = " ".join(card["payload"]["rubric"]) + f"\nfollowup={_key(card)}"
        self.assertTrue(exmod.grade(card, ans)["pass"])

    def test_empty_fails_with_nudge(self):
        res = exmod.grade(_card(), "   ")
        self.assertFalse(res["pass"])
        self.assertIn("Teach first", res["feedback"])

    def test_never_raises(self):
        res = promod.grade(None, None)
        self.assertFalse(res["pass"])
        res = promod.grade({}, object())
        self.assertFalse(res["pass"])


class EffectTest(unittest.TestCase):
    def test_due_widget_textarea(self):
        card = _card()
        out = cardsmod.answer_widget(
            {"id": "m:ex001", "exercise_type": "84",
             "payload": json.dumps(card["payload"])})
        self.assertIn("textarea", out)
        self.assertIn("Submit", out)

    def test_render_widget(self):
        out = exmod.render(_card())
        self.assertIn("Teach the junior", out)
        self.assertIn("How grading works", out)

    def test_disclosure(self):
        self.assertIn("follow-up", gradingmod.disclosure(84))


if __name__ == "__main__":
    unittest.main()
