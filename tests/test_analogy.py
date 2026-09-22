"""Tests for analogy-builder drills (type 86, F-82)."""
import json
import unittest

from groundwork import analogy as anmod
from groundwork import cards as cardsmod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod


def _concept(name="add"):
    return type("C", (), {"name": name, "node_id": f"calc.py:{name}",
                          "kind": "function", "file": "calc.py",
                          "line": 1})()


def _snippet():
    return ["def add(a, b):", "    total = a + b", "    return total"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(86, "ex001", _concept(), _snippet(), {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (86, "analogy-builder", "explain"))
        self.assertTrue(card["payload"]["grounded"])
        self.assertTrue(card["payload"]["domain"])
        self.assertTrue(card["payload"]["rubric"])

    def test_alias(self):
        a = anmod.generate("e1", _concept(), _snippet(), {})
        b = anmod.gen_analogy("e1", _concept(), _snippet(), {})
        self.assertEqual(a, b)

    def test_domain_stable_per_card(self):
        a = exmod.generate(86, "ex7", _concept(), _snippet(), {})
        b = exmod.generate(86, "ex7", _concept(), _snippet(), {})
        self.assertEqual(a["payload"]["domain"], b["payload"]["domain"])
        self.assertIn(a["payload"]["domain"], anmod._DOMAINS)

    def test_never_none(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _concept(), [], {})]:
            card = exmod.generate(86, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 86)

    def test_thin_input_ungrounded(self):
        thin = type("C", (), {"name": "", "node_id": "",
                              "kind": "", "file": "", "line": 0})()
        card = exmod.generate(86, "ex9", thin, [], {})
        self.assertFalse(card["payload"]["grounded"])


class GradeTest(unittest.TestCase):
    def _card(self):
        return exmod.generate(86, "ex001", _concept(), _snippet(), {})

    def test_half_bar_pass(self):
        card = self._card()
        ans = " ".join(card["payload"]["rubric"])
        res = exmod.grade(card, ans)
        self.assertTrue(res["pass"])

    def test_thin_fails_with_missing(self):
        card = self._card()
        res = exmod.grade(card, "something unrelated entirely")
        self.assertFalse(res["pass"])
        self.assertIn("missing", res["feedback"])

    def test_empty_fails(self):
        res = exmod.grade(self._card(), "   ")
        self.assertFalse(res["pass"])

    def test_never_raises(self):
        res = anmod.grade(None, None)
        self.assertFalse(res["pass"])


class EffectTest(unittest.TestCase):
    def test_due_widget_textarea_with_mapping_hint(self):
        card = exmod.generate(86, "ex001", _concept(), _snippet(), {})
        out = cardsmod.answer_widget(
            {"id": "m:ex001", "exercise_type": "86",
             "payload": json.dumps(card["payload"])})
        self.assertIn("textarea", out)
        self.assertIn("where it breaks", out)

    def test_render_widget(self):
        out = exmod.render(exmod.generate(
            86, "ex001", _concept(), _snippet(), {}))
        self.assertIn("where the analogy", out)
        self.assertIn("How grading works", out)

    def test_disclosure(self):
        self.assertIn("familiar domain", gradingmod.disclosure(86))


if __name__ == "__main__":
    unittest.main()
