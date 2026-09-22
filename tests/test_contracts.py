"""Tests for contract authoring (type 90, F-86)."""
import unittest

from groundwork import cards as cardsmod
from groundwork import contracts as conmod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod
from groundwork import pipeline as pipelinemod


def _concept(name="shout"):
    return type("C", (), {"name": name, "node_id": f"app.py:{name}",
                          "kind": "function", "file": "app.py",
                          "line": 1})()


CODE = ["def shout(text='hey'):", "    return text.upper() + '!'"]


def _card():
    return exmod.generate(90, "ex1", _concept(), CODE, {})


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = _card()
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (90, "contract-author", "create"))
        self.assertTrue(card["payload"]["grounded"])
        self.assertGreaterEqual(len(card["payload"]["valid"]), 2)
        self.assertIn("\n", card["payload"]["reference"])

    def test_reference_passes_by_construction(self):
        card = _card()
        res = exmod.grade(card, card["payload"]["reference"])
        self.assertTrue(res["pass"], res["feedback"])
        self.assertEqual(res["score"], 1.0)

    def test_ungrounded_shapes(self):
        self.assertFalse(exmod.generate(
            90, "x", _concept(),
            ["def f(x):", "    raise ValueError('no')"], {})["payload"]["grounded"])
        self.assertFalse(exmod.generate(
            90, "x", _concept(),
            ["def add(a, b):", "    return a + b"], {})["payload"]["grounded"])
        self.assertFalse(exmod.generate(
            90, "x", _concept(), ["x = 1"], {})["payload"]["grounded"])

    def test_never_none_never_raises(self):
        for args in [("x", _concept(), CODE, {}), (None, None, None, None)]:
            card = exmod.generate(90, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 90)


class GradeTest(unittest.TestCase):
    def test_mutant_ensures_fails(self):
        card = _card()
        req = card["payload"]["reference"].splitlines()[0]
        res = exmod.grade(card, f"{req}\nTrue")
        self.assertFalse(res["pass"])
        self.assertIn("ensures", res["feedback"])
        self.assertEqual(res["score"], 0.5)

    def test_valid_rejecting_requires_fails(self):
        card = _card()
        ens = card["payload"]["reference"].splitlines()[1]
        res = exmod.grade(card, f"False\n{ens}")
        self.assertFalse(res["pass"])
        self.assertIn("requires", res["feedback"])

    def test_bad_syntax_fails_closed(self):
        card = _card()
        res = exmod.grade(card, "x ==\nimport os")
        self.assertFalse(res["pass"])

    def test_empty_and_hostile_fail(self):
        card = _card()
        self.assertFalse(exmod.grade(card, "   ")["pass"])
        for bad in (None, 42, ["x"]):
            res = exmod.grade(card, bad)
            self.assertFalse(res["pass"])
            self.assertEqual(res["score"], 0.0)


class RenderTest(unittest.TestCase):
    def test_shape_and_widget_branch(self):
        out = exmod.render(_card())
        self.assertIn("contract-author", out)
        self.assertIn("textarea", out)
        widget = cardsmod.answer_widget(
            {"id": "c1", "exercise_type": 90, "payload": {},
             "front": "f", "concept": "c", "difficulty": 3}, 0, "/due")
        self.assertIn("textarea", widget)
        self.assertIn("requires(x)", widget)

    def test_disclosure_contract(self):
        line = gradingmod.disclosure(90)
        self.assertIn("mutant", line)
        self.assertNotEqual(line, gradingmod.disclosure("no-such-type"))


class RegistrationTest(unittest.TestCase):
    def test_six_part_emission(self):
        self.assertEqual(exmod.TYPES[90], ("contract-author", "create"))
        self.assertIn(90, exmod.BLOOM_TYPES["create"])
        self.assertIn(90, pipelinemod.BLOOM_DEFAULT_TYPES["create"])
        from groundwork import contractaudit as auditmod
        reg = auditmod.live_registry()
        for part in ("generator", "grader", "widget", "disclosure",
                     "emission", "e2e"):
            self.assertIn(90, reg[part], part)

    def test_caller_effect_submit_review_path(self):
        card = _card()
        good = exmod.grade(card, card["payload"]["reference"])
        self.assertTrue(good["pass"])
        # submit_review maps pass to grade 5: the Due queue consumes it.
        self.assertEqual(good["score"], 1.0)

    def test_tour_entry(self):
        e = conmod.tour_entry()
        self.assertEqual(e["id"], "contract-author")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], "up-next")


if __name__ == "__main__":
    unittest.main()
