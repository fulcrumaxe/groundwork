"""Tests for Feynman-check drills (type 85, F-81)."""
import unittest

from groundwork import exercises as exmod
from groundwork import feynman as feymod
from groundwork import grading as gradingmod


def _concept(name="add"):
    return type("C", (), {"name": name, "node_id": f"calc.py:{name}",
                          "kind": "function", "file": "calc.py",
                          "line": 1})()


def _snippet():
    return ["def add(a, b):", "    total = a + b", "    return total"]


class JargonTest(unittest.TestCase):
    def test_hits_case_insensitive_whole_word(self):
        self.assertEqual(
            feymod.jargon_hits("Leverage the PARADIGM daily"), ["leverage", "paradigm"])
        self.assertEqual(feymod.jargon_hits("functions loop calls"), [])
        self.assertEqual(feymod.jargon_hits(None), [])
        self.assertEqual(feymod.jargon_hits(42), [])

    def test_phrase_hit(self):
        self.assertIn("deep dive", feymod.jargon_hits("a deep dive into add"))

    def test_clarity_report(self):
        rep = feymod.clarity_report("add totals two numbers via leverage")
        self.assertEqual(rep["total_words"], 6)
        self.assertEqual(rep["hits"], ["leverage"])
        self.assertLess(rep["plain_ratio"], 1.0)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(85, "ex001", _concept(), _snippet(), {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (85, "feynman-check", "explain"))
        self.assertTrue(card["front"])
        self.assertTrue(card["payload"]["grounded"])
        self.assertTrue(card["payload"]["rubric"])

    def test_never_none(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _concept(), [], {})]:
            card = exmod.generate(85, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 85)

    def test_thin_input_ungrounded(self):
        card = exmod.generate(85, "ex9", _concept(), [], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = exmod.generate(85, "e1", _concept(), _snippet(), {})
        b = exmod.generate(85, "e1", _concept(), _snippet(), {})
        self.assertEqual(a, b)


class GradeTest(unittest.TestCase):
    def _card(self):
        return exmod.generate(85, "ex001", _concept(), _snippet(), {})

    def test_plain_explanation_passes(self):
        card = self._card()
        ans = " ".join(card["payload"]["rubric"]) + " plain and simple"
        res = exmod.grade(card, ans)
        self.assertTrue(res["pass"])

    def test_jargon_stuffed_halved_and_fails(self):
        card = self._card()
        plain = " ".join(card["payload"]["rubric"])
        res_plain = exmod.grade(card, plain + " plain and simple")
        res_jargon = exmod.grade(
            card, plain + " leverage the polymorphic callback paradigm synergy")
        self.assertTrue(res_plain["pass"])
        self.assertFalse(res_jargon["pass"])
        self.assertAlmostEqual(res_jargon["score"], res_plain["score"] / 2)
        self.assertIn("leverage", res_jargon["feedback"])

    def test_empty_fails_with_prompt(self):
        res = exmod.grade(self._card(), "   ")
        self.assertFalse(res["pass"])
        self.assertIn("plainly", res["feedback"])

    def test_never_raises(self):
        res = feymod.grade(None, None)
        self.assertFalse(res["pass"])


class RenderTest(unittest.TestCase):
    def test_widget_shape(self):
        card = exmod.generate(85, "ex001", _concept(), _snippet(), {})
        out = exmod.render(card)
        self.assertIn("textarea", out)
        self.assertIn("jargon", out)
        self.assertIn("How grading works", out)


class DisclosureTest(unittest.TestCase):
    def test_disclosure(self):
        self.assertIn("plain words", gradingmod.disclosure(85))


if __name__ == "__main__":
    unittest.main()
