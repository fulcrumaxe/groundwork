"""Tests for counterexample-hunt drills (type 87, F-83)."""
import unittest

from groundwork import counterex as cemod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod


def _concept(name="clamp"):
    return type("C", (), {"name": name, "node_id": f"calc.py:{name}",
                          "kind": "function", "file": "calc.py",
                          "line": 1})()


def _snippet():
    return ["def clamp(x):",
            "    total = x + 1",
            "    return total"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(87, "ex001", _concept(), _snippet(), {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (87, "counterexample-hunt", "analyse"))
        self.assertTrue(card["front"])
        self.assertIn("grounded", card["payload"])

    def test_never_none_never_raises(self):
        for args in [("x", _concept(), _snippet(), {}),
                     ("x", _concept(), _snippet(), {"commit": "abc"}),
                     (None, None, None, None)]:
            card = exmod.generate(87, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 87)

    def test_thin_input_ungrounded(self):
        card = exmod.generate(87, "ex9", _concept(""), [], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = exmod.generate(87, "e1", _concept(), _snippet(), {})
        b = exmod.generate(87, "e1", _concept(), _snippet(), {})
        self.assertEqual(a["payload"], b["payload"])

    def test_reference_breaks_claim_when_grounded(self):
        card = exmod.generate(87, "ex001", _concept(), _snippet(), {})
        self.assertTrue(card["payload"]["grounded"])
        res = exmod.grade(card, card["payload"]["reference"])
        self.assertTrue(res["pass"], res)


class GradeTest(unittest.TestCase):
    def _card(self):
        card = exmod.generate(87, "ex001", _concept(), _snippet(), {})
        if not card["payload"]["grounded"]:
            self.skipTest("no breaker for this seed rotation")
        return card

    def test_round_trip_pass(self):
        card = self._card()
        res = exmod.grade(card, card["payload"]["reference"])
        self.assertTrue(res["pass"])
        self.assertEqual(res["score"], 1.0)

    def test_claim_surviving_fails(self):
        # Deterministic unit: truthy claim on `pos`, no seed involved.
        ex = {"type": 87,
              "payload": {"func": "pos", "arity": 1,
                          "code": "def pos(x):\n    return x",
                          "check": "truthy", "reference": "0"}}
        broke = exmod.grade(ex, "0")
        self.assertTrue(broke["pass"])
        survived = exmod.grade(ex, "1")
        self.assertFalse(survived["pass"])
        self.assertEqual(survived["score"], 0.0)
        self.assertIn("survives", survived["feedback"])

    def test_empty_and_garbage_fail_closed(self):
        card = self._card()
        for bad in ("", "   ", "def broken(:", None):
            res = exmod.grade(card, bad)
            self.assertFalse(res["pass"])

    def test_never_raises(self):
        res = cemod.grade(None, None)
        self.assertFalse(res["pass"])
        res = cemod.grade({}, object())
        self.assertFalse(res["pass"])


class RenderTest(unittest.TestCase):
    def test_widget_shape(self):
        card = exmod.generate(87, "ex001", _concept(), _snippet(), {})
        out = exmod.render(card)
        self.assertIn("name='answer'", out)
        self.assertIn("How grading works", out)
        self.assertIn("calc.py:1", out)

    def test_escaping(self):
        card = exmod.generate(87, "ex001", _concept("<b>"), _snippet(), {})
        out = exmod.render(card)
        self.assertNotIn("<b>", out)


class DisclosureTest(unittest.TestCase):
    def test_disclosure(self):
        self.assertIn("breaks the claim", gradingmod.disclosure(87))


class LegacyTest(unittest.TestCase):
    def test_registry_shape(self):
        self.assertEqual(exmod.TYPES[1], ("flashcard", "recall"))
        self.assertEqual(exmod.TYPES[80][0], "naming-fluency")
        self.assertEqual(
            gradingmod.disclosure(4), "Exact file text — pick where it lives.")


if __name__ == "__main__":
    unittest.main()
