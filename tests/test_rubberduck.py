"""Tests for rubber-duck drills (type 83, F-79)."""
import unittest

from groundwork import cards as cardsmod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod
from groundwork import rubberduck as rdmod


def _concept(name="add"):
    return type("C", (), {"name": name, "node_id": f"calc.py:{name}",
                          "kind": "function", "file": "calc.py",
                          "line": 1})()


def _snippet():
    return ["def add(a, b):", "    total = a + b", "    return total"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(83, "ex001", _concept(), _snippet(), {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (83, "rubber-duck", "explain"))
        self.assertEqual(len(card["payload"]["questions"]), 3)
        self.assertTrue(card["payload"]["grounded"])

    def test_never_none(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _concept(), [], {})]:
            card = exmod.generate(83, *args)
            self.assertIsNotNone(card)
            self.assertTrue(card["front"] and card["back"])

    def test_thin_input_ungrounded(self):
        card = exmod.generate(83, "ex9", _concept(), [], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = exmod.generate(83, "e1", _concept(), _snippet(), {})
        b = exmod.generate(83, "e1", _concept(), _snippet(), {})
        self.assertEqual(a, b)

    def test_disclosure_contract(self):
        self.assertIn("three questions", rdmod.disclosure())
        self.assertIn("half", rdmod.disclosure())


class GradeTest(unittest.TestCase):
    def _card(self):
        return exmod.generate(83, "ex001", _concept(), _snippet(), {})

    def test_round_trip_pass(self):
        card = self._card()
        ans = " ".join(card["payload"]["rubric"])
        res = exmod.grade(card, ans)
        self.assertTrue(res["pass"])
        self.assertGreaterEqual(res["score"], 0.5)

    def test_fail_closed(self):
        card = self._card()
        for bad in ("", "   ", None, "unrelated weather report"):
            res = exmod.grade(card, bad)
            self.assertFalse(res["pass"])
            self.assertIn("score", res)
        thin = exmod.grade(card, card["payload"]["rubric"][0])
        self.assertIn("missing", thin["feedback"])

    def test_never_raises(self):
        res = rdmod.grade(None, None)
        self.assertFalse(res["pass"])
        res = rdmod.grade({}, object())
        self.assertFalse(res["pass"])


class EffectTest(unittest.TestCase):
    def test_due_widget_has_questions_and_submit(self):
        import json
        card = exmod.generate(83, "ex001", _concept(), _snippet(), {})
        out = cardsmod.answer_widget(
            {"id": "m:ex001", "exercise_type": "83",
             "payload": json.dumps(card["payload"])})
        self.assertIn("textarea", out)
        self.assertIn("Submit", out)

    def test_disclosure_table(self):
        self.assertIn("three questions", gradingmod.disclosure(83))

    def test_render_widget(self):
        card = exmod.generate(83, "ex001", _concept(), _snippet(), {})
        out = exmod.render(card)
        self.assertIn("Q1", out)
        self.assertIn("Explain to the duck", out)


if __name__ == "__main__":
    unittest.main()
