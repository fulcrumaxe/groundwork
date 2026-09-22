"""Tests for boundary-value drills (type 88, F-84)."""
import unittest

from groundwork import boundary as boundmod
from groundwork import exercises as exmod
from groundwork import grading as gradingmod


def _concept(name="check"):
    return type("C", (), {"name": name, "node_id": f"app.py:{name}",
                          "kind": "function", "file": "app.py",
                          "line": 1})()


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(
            88, "ex001", _concept(), ["def check(x):", "    return x < 10"], {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (88, "boundary-drill", "analyse"))
        self.assertTrue(card["front"])
        self.assertIn("grounded", card["payload"])

    def test_compare_and_range_sites(self):
        card = exmod.generate(
            88, "ex1", _concept(),
            ["def check(x):", "    return x < 10"], {})
        self.assertTrue(card["payload"]["grounded"])
        self.assertEqual(card["payload"]["answer"], "10")
        self.assertEqual(card["payload"]["kind"], "compare")
        card = exmod.generate(
            88, "ex2", _concept(), ["for i in range(10):", "    use(i)"], {})
        self.assertTrue(card["payload"]["grounded"])
        self.assertEqual(card["payload"]["answer"], "10")
        self.assertEqual(card["payload"]["kind"], "range")

    def test_distractors_are_neighbours(self):
        card = exmod.generate(
            88, "ex1", _concept(),
            ["def check(x):", "    return x < 10"], {})
        self.assertEqual(sorted(card["payload"]["choices"]), ["10", "11", "9"])

    def test_len_counts_and_negative_literals(self):
        card = exmod.generate(
            88, "ex1", _concept(),
            ["def ok(xs):", "    return len(xs) > 0"], {})
        self.assertEqual(card["payload"]["answer"], "0")
        card = exmod.generate(
            88, "ex2", _concept(),
            ["def neg(x):", "    return x >= -3"], {})
        self.assertEqual(card["payload"]["answer"], "-3")

    def test_never_none_never_raises(self):
        for args in [("x", _concept(), ["def f(x):", "    return x < 2"], {}),
                     (None, None, None, None)]:
            card = exmod.generate(88, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 88)

    def test_thin_input_ungrounded(self):
        card = exmod.generate(88, "ex9", _concept(), ["x = 1"], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = exmod.generate(
            88, "e1", _concept(), ["def f(x):", "    return x < 4"], {})
        b = exmod.generate(
            88, "e1", _concept(), ["def f(x):", "    return x < 4"], {})
        self.assertEqual(a, b)


class GradeTest(unittest.TestCase):
    def _card(self):
        return exmod.generate(
            88, "ex001", _concept(),
            ["def check(x):", "    return x < 10"], {})

    def test_exact_edge_passes(self):
        res = exmod.grade(self._card(), "10")
        self.assertTrue(res["pass"])
        self.assertEqual(res["score"], 1.0)

    def test_first_integer_token_wins(self):
        res = exmod.grade(self._card(), "I think 10 is the edge")
        self.assertTrue(res["pass"])

    def test_neighbour_fails_without_partial(self):
        for bad in ("9", "11", "edge"):
            res = exmod.grade(self._card(), bad)
            self.assertFalse(res["pass"])
            self.assertEqual(res["score"], 0.0)

    def test_empty_fails(self):
        res = exmod.grade(self._card(), "   ")
        self.assertFalse(res["pass"])

    def test_never_raises(self):
        res = boundmod.grade(None, None)
        self.assertFalse(res["pass"])
        res = boundmod.grade({}, object())
        self.assertFalse(res["pass"])


class RenderTest(unittest.TestCase):
    def test_widget_shape(self):
        card = exmod.generate(
            88, "ex001", _concept(),
            ["def check(x):", "    return x < 10"], {})
        out = exmod.render(card)
        self.assertIn("Probe it", out)
        self.assertIn("How grading works", out)
        self.assertIn("app.py:1", out)

    def test_escaping(self):
        card = exmod.generate(
            88, "ex001", _concept("<b>"),
            ["def f(x):", "    return x < 1"], {})
        out = exmod.render(card)
        self.assertNotIn("<b>", out)


class DisclosureTest(unittest.TestCase):
    def test_disclosure(self):
        self.assertIn("boundary value", gradingmod.disclosure(88))
        self.assertIn("boundary value", boundmod.disclosure())


if __name__ == "__main__":
    unittest.main()
