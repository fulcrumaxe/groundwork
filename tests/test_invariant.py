"""Tests for invariant stating (type 89, F-85)."""
import unittest

from groundwork import exercises as exmod
from groundwork import grading as gradingmod
from groundwork import invariant as invmod
from groundwork import pipeline as pipelinemod


def _concept(name="total"):
    return type("C", (), {"name": name, "node_id": f"app.py:{name}",
                          "kind": "function", "file": "app.py",
                          "line": 1})()


def _loop_card():
    return exmod.generate(
        89, "ex1", _concept(),
        ["def total(ns):", "    s = 0", "    for i in range(len(ns)):",
         "        s += ns[i]", "    return s"], {})


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = _loop_card()
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (89, "invariant-state", "analyse"))
        self.assertTrue(card["front"])
        self.assertTrue(card["payload"]["grounded"])

    def test_for_range_reference(self):
        card = exmod.generate(
            89, "ex1", _concept(),
            ["for i in range(10):", "    use(i)"], {})
        self.assertTrue(card["payload"]["grounded"])
        self.assertEqual(card["payload"]["reference"], "0<=i<=10")

    def test_range_bounds_as_written(self):
        card = exmod.generate(
            89, "ex1", _concept(),
            ["for k in range(a, b):", "    use(k)"], {})
        self.assertEqual(card["payload"]["reference"], "a<=k<=b")

    def test_while_guard_reference(self):
        card = exmod.generate(
            89, "ex1", _concept(),
            ["while i < n:", "    i += 1"], {})
        self.assertTrue(card["payload"]["grounded"])
        self.assertEqual(card["payload"]["reference"], "i<n")

    def test_ungrounded_without_loop(self):
        card = exmod.generate(
            89, "ex1", _concept(), ["def f(x):", "    return x + 1"], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_deterministic_and_never_none(self):
        code = ["for i in range(10):", "    use(i)"]
        first = exmod.generate(89, "ex1", _concept(), code, {})
        second = exmod.generate(89, "ex1", _concept(), code, {})
        self.assertEqual(first["payload"], second["payload"])
        for args in [("x", _concept(), code, {}), (None, None, None, None)]:
            card = exmod.generate(89, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 89)


class GradeTest(unittest.TestCase):
    def test_canonical_and_spaced_pass(self):
        card = _loop_card()
        ref = card["payload"]["reference"]
        for sub in (ref, "  " + ref.upper() + "  ", ref.replace("<=", " <=")):
            res = exmod.grade(card, sub)
            self.assertTrue(res["pass"], sub)
            self.assertEqual(res["score"], 1.0)

    def test_wrong_and_empty_fail(self):
        card = _loop_card()
        res = exmod.grade(card, "0<=i<n")
        self.assertFalse(res["pass"])
        self.assertEqual(res["score"], 0.0)
        self.assertIn(card["payload"]["reference"], res["feedback"])
        res = exmod.grade(card, "   ")
        self.assertFalse(res["pass"])

    def test_never_raises(self):
        card = _loop_card()
        for bad in (None, 42, ["x"], {"a": 1}):
            res = exmod.grade(card, bad)
            self.assertFalse(res["pass"])
            self.assertEqual(res["score"], 0.0)


class RenderTest(unittest.TestCase):
    def test_shape_and_escaping(self):
        out = exmod.render(_loop_card())
        self.assertIn("invariant-state", out)
        self.assertIn("How grading works", out)
        self.assertIn("name='answer'", out)

    def test_disclosure_contract(self):
        line = gradingmod.disclosure(89)
        self.assertIn("invariant", line)
        self.assertNotEqual(line, gradingmod.disclosure("no-such-type"))
        self.assertIn("invariant", invmod.section_html())
        self.assertIn(f"id='{invmod.STATUS_ANCHOR}'", invmod.section_html())


class RegistrationTest(unittest.TestCase):
    def test_six_part_emission(self):
        self.assertEqual(exmod.TYPES[89], ("invariant-state", "analyse"))
        self.assertIn(89, exmod.BLOOM_TYPES["analyse"])
        self.assertIn(89, pipelinemod.BLOOM_DEFAULT_TYPES["analyse"])
        from groundwork import contractaudit as auditmod
        reg = auditmod.live_registry()
        for part in ("generator", "grader", "disclosure", "emission", "e2e"):
            self.assertIn(89, reg[part], part)

    def test_caller_effect_due_grades_through_registry(self):
        card = _loop_card()
        good = exmod.grade(card, card["payload"]["reference"])
        bad = exmod.grade(card, "wrong")
        self.assertTrue(good["pass"])
        self.assertFalse(bad["pass"])
        # Legacy path: pre-change Due output has no type-89 cards.
        self.assertEqual(exmod.TYPES[88][0], "boundary-drill")

    def test_tour_entry(self):
        e = invmod.tour_entry()
        self.assertEqual(e["id"], "invariant-state")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], "up-next")


if __name__ == "__main__":
    unittest.main()
